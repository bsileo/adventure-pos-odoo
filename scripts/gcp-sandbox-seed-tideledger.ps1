#requires -Version 5.1
<#
.SYNOPSIS
  Seed or refresh Tideledger on the shared GCP sandbox (non-destructive).

.DESCRIPTION
  SSHs to the sandbox VM and runs scripts/gcp-sandbox-seed-tideledger.sh.
  Does not wipe Postgres. Use -ResetSeed to recreate scenario seed records.

.EXAMPLE
  $env:GCP_SANDBOX_SSH_HOST = '203.0.113.50'
  .\scripts\gcp-sandbox-seed-tideledger.ps1

.EXAMPLE
  .\scripts\gcp-sandbox-seed-tideledger.ps1 -ResetSeed
#>
param(
    [string] $SshHost = $env:GCP_SANDBOX_SSH_HOST,
    [string] $DeployPath = $(if ($env:GCP_SANDBOX_DEPLOY_PATH) { $env:GCP_SANDBOX_DEPLOY_PATH } else { '/srv/adventurepos/adventure-pos-odoo' }),
    [string] $SshUser = 'deploy',
    [switch] $ResetSeed
)

if (-not $SshHost) {
    Write-Error "Set GCP_SANDBOX_SSH_HOST to the sandbox VM IP or hostname, or pass -SshHost."
    exit 1
}

$remoteArgs = ''
if ($ResetSeed) {
    $remoteArgs = ' --reset-seed'
}

ssh -t "${SshUser}@${SshHost}" "cd '$DeployPath' && bash ./scripts/gcp-sandbox-seed-tideledger.sh$remoteArgs"
