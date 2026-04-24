#requires -Version 5.1
<#
.SYNOPSIS
  Manage a developer-owned Adventure POS GCP VM for remote development.

.DESCRIPTION
  Start, stop, inspect, and connect Cursor/SSH to a remote dev VM that runs the
  Docker-based Odoo + Postgres stack. Run from your PC, not on the VM itself.
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('init-ssh', 'create', 'start', 'stop', 'status', 'ip', 'url', 'open', 'ssh', 'cursor', 'up', 'init-db', 'bootstrap')]
    [string] $Action = 'status'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-DefaultRemoteDevUser {
    if ($env:REMOTE_DEV_USER) { return $env:REMOTE_DEV_USER }
    if ($env:USERNAME) { return $env:USERNAME }
    return [Environment]::UserName
}

function Convert-ToGceNamePart {
    param([string]$Value)
    $normalized = $Value.ToLowerInvariant() -replace '[^a-z0-9-]', '-'
    $normalized = $normalized -replace '-+', '-'
    $normalized = $normalized.Trim('-')
    if (-not $normalized) { $normalized = 'dev' }
    if ($normalized.Length -gt 40) {
        $normalized = $normalized.Substring(0, 40).Trim('-')
    }
    return $normalized
}

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

function Get-InstanceIp {
    & gcloud compute instances describe $script:Instance `
        --zone=$script:Zone `
        --project=$script:Project `
        --format='value(networkInterfaces[0].accessConfigs[0].natIP)'
}

function Test-InstanceExists {
    & gcloud compute instances describe $script:Instance `
        --zone=$script:Zone `
        --project=$script:Project `
        --format='value(name)' 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Assert-InstanceExists {
    if (-not (Test-InstanceExists)) {
        throw "Remote dev VM '$script:Instance' was not found in $script:Project/$script:Zone. Run '.\scripts\remote-dev.ps1 create' first, or set REMOTE_DEV_GCP_INSTANCE to an existing VM."
    }
}

function Resolve-SshPublicKeyPath {
    if ($env:REMOTE_DEV_SSH_PUBLIC_KEY_PATH) {
        return $env:REMOTE_DEV_SSH_PUBLIC_KEY_PATH
    }

    $homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    $candidates = @(
        (Join-Path $homeDir '.ssh\id_ed25519.pub'),
        (Join-Path $homeDir '.ssh\id_rsa.pub')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "No SSH public key found. Run '.\scripts\remote-dev.ps1 init-ssh', set REMOTE_DEV_SSH_PUBLIC_KEY_PATH, or create ~/.ssh/id_ed25519.pub."
}

function Initialize-SshKey {
    Assert-Command ssh-keygen

    $homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    $sshDir = Join-Path $homeDir '.ssh'
    $privateKeyPath = Join-Path $sshDir 'id_ed25519'
    $publicKeyPath = Join-Path $sshDir 'id_ed25519.pub'

    if (Test-Path $publicKeyPath) {
        Write-Host "SSH public key already exists: $publicKeyPath"
        return
    }

    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    & ssh-keygen -t ed25519 -f $privateKeyPath -N ""
    Write-Host "Created SSH key pair:"
    Write-Host "  Private: $privateKeyPath"
    Write-Host "  Public:  $publicKeyPath"
}

function New-MetadataSshKeysFile {
    $pubKeyPath = Resolve-SshPublicKeyPath
    $pubKey = (Get-Content -Path $pubKeyPath -Raw).Trim()
    if (-not $pubKey) {
        throw "SSH public key file '$pubKeyPath' is empty."
    }

    $tempFile = Join-Path ([System.IO.Path]::GetTempPath()) ("adventurepos-remote-dev-" + [System.Guid]::NewGuid().ToString() + ".txt")
    Set-Content -Path $tempFile -Value "${VmUser}:$pubKey" -NoNewline
    return $tempFile
}

function Test-FirewallRuleExists {
    & gcloud compute firewall-rules describe $script:FirewallRule `
        --project=$script:Project `
        --format='value(name)' 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Ensure-FirewallRule {
    if (Test-FirewallRuleExists) {
        Write-Host "Firewall rule '$FirewallRule' already exists."
        return
    }

    & gcloud compute firewall-rules create $FirewallRule `
        --project=$Project `
        --direction=INGRESS `
        --allow="tcp:$OdooPort" `
        --target-tags=$NetworkTags `
        --source-ranges=$OdooSourceRanges `
        --description="Allow Adventure POS remote dev Odoo access on port $OdooPort"
}

function Get-SshArgs {
    $args = @('-o', 'StrictHostKeyChecking=accept-new')
    if ($script:SshKey) {
        $args += @('-i', $script:SshKey)
    }
    return $args
}

function Invoke-RemoteCommand {
    param([string]$Command)
    $ip = Get-InstanceIp
    if (-not $ip) {
        throw "Instance '$script:Instance' does not have a public IP yet."
    }
    $sshArgs = Get-SshArgs
    & ssh @sshArgs "$script:VmUser@$ip" $Command
}

$Project = if ($env:REMOTE_DEV_GCP_PROJECT) { $env:REMOTE_DEV_GCP_PROJECT } else { 'adventure-pos-sandbox' }
$Zone = if ($env:REMOTE_DEV_GCP_ZONE) { $env:REMOTE_DEV_GCP_ZONE } else { 'us-central1-a' }
$InstancePrefix = if ($env:REMOTE_DEV_INSTANCE_PREFIX) { $env:REMOTE_DEV_INSTANCE_PREFIX } else { 'adventurepos-dev' }
$InstanceUser = Convert-ToGceNamePart (Get-DefaultRemoteDevUser)
$Instance = if ($env:REMOTE_DEV_GCP_INSTANCE) { $env:REMOTE_DEV_GCP_INSTANCE } else { "$InstancePrefix-$InstanceUser" }
$VmUser = if ($env:REMOTE_DEV_VM_USER) { $env:REMOTE_DEV_VM_USER } else { 'deploy' }
$RepoPath = if ($env:REMOTE_DEV_REPO_PATH) { $env:REMOTE_DEV_REPO_PATH } else { '/srv/adventurepos/adventure-pos-odoo' }
$RepoUrl = if ($env:REMOTE_DEV_REPO_URL) { $env:REMOTE_DEV_REPO_URL } else { 'git@github.com:bsileo/adventure-pos-odoo.git' }
$RepoBranch = if ($env:REMOTE_DEV_REPO_BRANCH) { $env:REMOTE_DEV_REPO_BRANCH } else { 'develop' }
$OdooPort = if ($env:REMOTE_DEV_ODOO_PORT) { $env:REMOTE_DEV_ODOO_PORT } else { '8069' }
$SshKey = if ($env:REMOTE_DEV_SSH_KEY) { $env:REMOTE_DEV_SSH_KEY } else { '' }
$MachineType = if ($env:REMOTE_DEV_MACHINE_TYPE) { $env:REMOTE_DEV_MACHINE_TYPE } else { 'e2-standard-2' }
$BootDiskSize = if ($env:REMOTE_DEV_BOOT_DISK_SIZE) { $env:REMOTE_DEV_BOOT_DISK_SIZE } else { '50GB' }
$ImageFamily = if ($env:REMOTE_DEV_IMAGE_FAMILY) { $env:REMOTE_DEV_IMAGE_FAMILY } else { 'ubuntu-2204-lts' }
$ImageProject = if ($env:REMOTE_DEV_IMAGE_PROJECT) { $env:REMOTE_DEV_IMAGE_PROJECT } else { 'ubuntu-os-cloud' }
$NetworkTags = if ($env:REMOTE_DEV_NETWORK_TAGS) { $env:REMOTE_DEV_NETWORK_TAGS } else { 'adventurepos-remote-dev' }
$FirewallRule = if ($env:REMOTE_DEV_FIREWALL_RULE) { $env:REMOTE_DEV_FIREWALL_RULE } else { 'adventurepos-remote-dev-odoo' }
$OdooSourceRanges = if ($env:REMOTE_DEV_ODOO_SOURCE_RANGES) { $env:REMOTE_DEV_ODOO_SOURCE_RANGES } else { '0.0.0.0/0' }

switch ($Action) {
    'init-ssh' {
        Initialize-SshKey
    }
    'create' {
        Assert-Command gcloud
        if (Test-InstanceExists) {
            Write-Host "Remote dev VM '$Instance' already exists."
        } else {
            $metadataFile = New-MetadataSshKeysFile
            try {
                & gcloud compute instances create $Instance `
                    --zone=$Zone `
                    --project=$Project `
                    --machine-type=$MachineType `
                    --boot-disk-size=$BootDiskSize `
                    --image-family=$ImageFamily `
                    --image-project=$ImageProject `
                    --tags=$NetworkTags `
                    --metadata-from-file "ssh-keys=$metadataFile"
            } finally {
                Remove-Item $metadataFile -ErrorAction SilentlyContinue
            }
        }
        Ensure-FirewallRule
        Write-Host ''
        Write-Host "Next steps:"
        Write-Host "  1. .\scripts\remote-dev.ps1 start"
        Write-Host "  2. .\scripts\remote-dev.ps1 bootstrap"
        Write-Host "  3. .\scripts\remote-dev.ps1 cursor"
    }
    'start' {
        Assert-Command gcloud
        Assert-InstanceExists
        & gcloud compute instances start $Instance --zone=$Zone --project=$Project
        $ip = Get-InstanceIp
        Write-Host ''
        Write-Host "Odoo URL: http://$($ip):$OdooPort"
        Write-Host 'Cursor hint: .\scripts\remote-dev.ps1 cursor'
    }
    'stop' {
        Assert-Command gcloud
        Assert-InstanceExists
        & gcloud compute instances stop $Instance --zone=$Zone --project=$Project
    }
    'status' {
        Assert-Command gcloud
        Assert-InstanceExists
        & gcloud compute instances describe $Instance --zone=$Zone --project=$Project --format='value(status)'
    }
    'ip' {
        Assert-Command gcloud
        Assert-InstanceExists
        Get-InstanceIp
    }
    'url' {
        Assert-Command gcloud
        Assert-InstanceExists
        Write-Output "http://$(Get-InstanceIp):$OdooPort"
    }
    'open' {
        Assert-Command gcloud
        Assert-InstanceExists
        $url = "http://$(Get-InstanceIp):$OdooPort"
        Start-Process $url
    }
    'ssh' {
        Assert-Command gcloud
        Assert-Command ssh
        Assert-InstanceExists
        $ip = Get-InstanceIp
        if (-not $ip) {
            throw "Instance '$Instance' does not have a public IP yet."
        }
        $sshArgs = Get-SshArgs
        & ssh @sshArgs "$VmUser@$ip"
    }
    'cursor' {
        Assert-Command gcloud
        Assert-InstanceExists
        $ip = Get-InstanceIp
        Write-Host 'Cursor Remote SSH target:'
        Write-Host "  Host: $Instance"
        Write-Host "  HostName: $ip"
        Write-Host "  User: $VmUser"
        Write-Host "  Workspace path: $RepoPath"
        Write-Host ''
        Write-Host 'Suggested SSH config snippet:'
        Write-Host "Host $Instance"
        Write-Host "  HostName $ip"
        Write-Host "  User $VmUser"
        Write-Host '  StrictHostKeyChecking accept-new'
        if ($SshKey) {
            Write-Host "  IdentityFile $SshKey"
        }
    }
    'up' {
        Assert-Command gcloud
        Assert-Command ssh
        Assert-InstanceExists
        $remoteCommand = "cd $RepoPath && docker compose up -d && bash ./scripts/odoo-init-db.sh"
        Invoke-RemoteCommand $remoteCommand
    }
    'init-db' {
        Assert-Command gcloud
        Assert-Command ssh
        Assert-InstanceExists
        $remoteCommand = "cd $RepoPath && bash ./scripts/odoo-init-db.sh"
        Invoke-RemoteCommand $remoteCommand
    }
    'bootstrap' {
        Assert-Command gcloud
        Assert-Command ssh
        Assert-InstanceExists
        $ip = Get-InstanceIp
        if (-not $ip) {
            throw "Instance '$Instance' does not have a public IP yet."
        }
        $bootstrapPath = Join-Path $PSScriptRoot 'remote-dev-bootstrap.sh'
        $bootstrapScript = Get-Content -Path $bootstrapPath -Raw
        $sshArgs = Get-SshArgs
        $remoteBootstrapCommand = "bash -s -- $RepoUrl $RepoBranch $RepoPath"
        $bootstrapScript | & ssh @sshArgs "$VmUser@$ip" $remoteBootstrapCommand
    }
}
