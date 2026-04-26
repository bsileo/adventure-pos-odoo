#requires -Version 5.1
<#
.SYNOPSIS
  Open an interactive SSH session to reset the shared GCP sandbox Odoo database.

.DESCRIPTION
  Runs scripts/gcp-sandbox-reset-db.sh on the VM (requires TTY for confirmation).
  Set GCP_SANDBOX_SSH_HOST to the VM IP/hostname (same as GitHub secret).
  Optional: GCP_SANDBOX_DEPLOY_PATH if your clone is not the default.

.EXAMPLE
  $env:GCP_SANDBOX_SSH_HOST = '203.0.113.50'
  .\scripts\gcp-sandbox-reset-db.ps1
#>
param(
    [string] $SshHost = $env:GCP_SANDBOX_SSH_HOST,
    [string] $DeployPath = $(if ($env:GCP_SANDBOX_DEPLOY_PATH) { $env:GCP_SANDBOX_DEPLOY_PATH } else { '/srv/adventurepos/adventure-pos-odoo' }),
    [string] $SshUser = 'deploy'
)

if (-not $SshHost) {
    Write-Error "Set GCP_SANDBOX_SSH_HOST to the sandbox VM IP or hostname, or pass -SshHost."
    exit 1
}

ssh -t "${SshUser}@${SshHost}" "cd '$DeployPath' && bash ./scripts/gcp-sandbox-reset-db.sh"
