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
    [ValidateSet('create', 'start', 'stop', 'status', 'ip', 'url', 'open', 'tunnel', 'ssh', 'cursor', 'up', 'init-db', 'bootstrap', 'fetch-branch')]
    [string] $Action = 'status',

    [Parameter(Position = 1)]
    [string] $Branch,

    [switch] $Force
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
        --format='value(networkInterfaces[0].networkIP)'
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

function Invoke-RemoteCommand {
    param([string]$Command)
    & gcloud compute ssh $script:Instance `
        --zone=$script:Zone `
        --project=$script:Project `
        --tunnel-through-iap `
        --command=$Command
}

function Invoke-FetchBranch {
    param(
        [string] $BranchName,
        [switch] $ResetExistingBranch
    )

    if (-not $BranchName) {
        throw "Branch name is required. Example: .\scripts\remote-dev.ps1 fetch-branch feature/d360-customer-workflow"
    }

    Assert-Command git
    Assert-Command gcloud
    Assert-InstanceExists

    $remoteName = if ($env:REMOTE_DEV_FETCH_REMOTE) { $env:REMOTE_DEV_FETCH_REMOTE } else { 'gcp-dev' }
    & gcloud compute config-ssh --project=$Project --tunnel-through-iap --quiet
    $remoteUrl = "$Instance.$Zone.$Project`:$RepoPath"
    $existingRemotes = @(git remote)

    if ($existingRemotes -contains $remoteName) {
        $currentUrl = git remote get-url $remoteName
        if ($currentUrl -ne $remoteUrl) {
            git remote set-url $remoteName $remoteUrl
        }
    } else {
        git remote add $remoteName $remoteUrl
    }

    git fetch $remoteName $BranchName

    $localBranch = git branch --list $BranchName
    if ($localBranch) {
        if (-not $ResetExistingBranch) {
            throw "Local branch '$BranchName' already exists. Use -Force to reset it to the VM branch."
        }
        git branch -D $BranchName
    }

    git checkout -b $BranchName FETCH_HEAD
    git push -u origin $BranchName
}

$Project = if ($env:REMOTE_DEV_GCP_PROJECT) { $env:REMOTE_DEV_GCP_PROJECT } else { 'adventure-pos-sandbox' }
$Zone = if ($env:REMOTE_DEV_GCP_ZONE) { $env:REMOTE_DEV_GCP_ZONE } else { 'us-central1-a' }
$InstancePrefix = if ($env:REMOTE_DEV_INSTANCE_PREFIX) { $env:REMOTE_DEV_INSTANCE_PREFIX } else { 'adventurepos-dev' }
$InstanceUser = Convert-ToGceNamePart (Get-DefaultRemoteDevUser)
$Instance = if ($env:REMOTE_DEV_GCP_INSTANCE) { $env:REMOTE_DEV_GCP_INSTANCE } else { "$InstancePrefix-$InstanceUser" }
$RepoPath = if ($env:REMOTE_DEV_REPO_PATH) { $env:REMOTE_DEV_REPO_PATH } else { '/srv/adventurepos/adventure-pos-odoo' }
$RepoUrl = if ($env:REMOTE_DEV_REPO_URL) { $env:REMOTE_DEV_REPO_URL } else { 'git@github.com:bsileo/adventure-pos-odoo.git' }
$RepoBranch = if ($env:REMOTE_DEV_REPO_BRANCH) { $env:REMOTE_DEV_REPO_BRANCH } else { 'develop' }
$OdooPort = if ($env:REMOTE_DEV_ODOO_PORT) { $env:REMOTE_DEV_ODOO_PORT } else { '8069' }
$ServiceAccount = if ($env:REMOTE_DEV_SERVICE_ACCOUNT) { $env:REMOTE_DEV_SERVICE_ACCOUNT } else { "adventurepos-remote-dev-vm@$Project.iam.gserviceaccount.com" }
$AccessScopes = if ($env:REMOTE_DEV_ACCESS_SCOPES) { $env:REMOTE_DEV_ACCESS_SCOPES } else { 'cloud-platform' }
$MachineType = if ($env:REMOTE_DEV_MACHINE_TYPE) { $env:REMOTE_DEV_MACHINE_TYPE } else { 'e2-standard-2' }
$BootDiskSize = if ($env:REMOTE_DEV_BOOT_DISK_SIZE) { $env:REMOTE_DEV_BOOT_DISK_SIZE } else { '50GB' }
$ImageFamily = if ($env:REMOTE_DEV_IMAGE_FAMILY) { $env:REMOTE_DEV_IMAGE_FAMILY } else { 'ubuntu-2204-lts' }
$ImageProject = if ($env:REMOTE_DEV_IMAGE_PROJECT) { $env:REMOTE_DEV_IMAGE_PROJECT } else { 'ubuntu-os-cloud' }
$NetworkTags = if ($env:REMOTE_DEV_NETWORK_TAGS) { $env:REMOTE_DEV_NETWORK_TAGS } else { 'adventurepos-remote-dev,iap-ssh' }

switch ($Action) {
    'create' {
        Assert-Command gcloud
        if (Test-InstanceExists) {
            Write-Host "Remote dev VM '$Instance' already exists."
        } else {
            & gcloud compute instances create $Instance `
                --zone=$Zone `
                --project=$Project `
                --machine-type=$MachineType `
                --boot-disk-size=$BootDiskSize `
                --image-family=$ImageFamily `
                --image-project=$ImageProject `
                --service-account=$ServiceAccount `
                --scopes=$AccessScopes `
                --tags=$NetworkTags `
                --no-address `
                --metadata=enable-oslogin=TRUE,enable-oslogin-2fa=TRUE,block-project-ssh-keys=TRUE
        }
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
        Write-Host "Private IP: $ip"
        Write-Host 'Odoo URL after starting the tunnel: http://127.0.0.1:8069'
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
        Write-Output "http://127.0.0.1:$OdooPort"
    }
    'open' {
        Assert-Command gcloud
        Assert-InstanceExists
        $url = "http://127.0.0.1:$OdooPort"
        Start-Process $url
    }
    'tunnel' {
        Assert-Command gcloud
        Assert-InstanceExists
        & gcloud compute start-iap-tunnel $Instance $OdooPort `
            --local-host-port="127.0.0.1:$OdooPort" `
            --zone=$Zone `
            --project=$Project
    }
    'ssh' {
        Assert-Command gcloud
        Assert-InstanceExists
        & gcloud compute ssh $Instance --zone=$Zone --project=$Project --tunnel-through-iap
    }
    'cursor' {
        Assert-Command gcloud
        Assert-InstanceExists
        & gcloud compute config-ssh --project=$Project --tunnel-through-iap --quiet
        Write-Host 'Cursor Remote SSH configuration was updated by gcloud.'
        Write-Host "Connect to the generated host for $Instance.$Zone.$Project."
        Write-Host 'Open this exact folder in Cursor after connecting:'
        Write-Host "  $RepoPath"
        Write-Host ''
        Write-Host "Do not open $(Split-Path -Parent $RepoPath); it is only the parent folder and Source Control may not detect the nested repo."
        Write-Host ''
    }
    'up' {
        Assert-Command gcloud
        Assert-InstanceExists
        $remoteCommand = "cd $RepoPath && docker compose up -d && bash ./scripts/odoo-init-db.sh"
        Invoke-RemoteCommand $remoteCommand
    }
    'init-db' {
        Assert-Command gcloud
        Assert-InstanceExists
        $remoteCommand = "cd $RepoPath && bash ./scripts/odoo-init-db.sh"
        Invoke-RemoteCommand $remoteCommand
    }
    'bootstrap' {
        Assert-Command gcloud
        Assert-InstanceExists
        $bootstrapPath = Join-Path $PSScriptRoot 'remote-dev-bootstrap.sh'
        $bootstrapScript = Get-Content -Path $bootstrapPath -Raw
        $remoteBootstrapCommand = "bash -s -- $RepoUrl $RepoBranch $RepoPath"
        $bootstrapScript | & gcloud compute ssh $Instance `
            --zone=$Zone `
            --project=$Project `
            --tunnel-through-iap `
            --command=$remoteBootstrapCommand
    }
    'fetch-branch' {
        Invoke-FetchBranch -BranchName $Branch -ResetExistingBranch:$Force
    }
}
