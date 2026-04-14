#requires -Version 5.1
<#
.SYNOPSIS Start/stop/status/public IP for the shared Adventure POS GCP sandbox VM.
  Run from your PC (not on the VM). Requires gcloud CLI and project access.

  Examples:
    .\scripts\gcp-sandbox-vm.ps1 stop
    .\scripts\gcp-sandbox-vm.ps1 start
    .\scripts\gcp-sandbox-vm.ps1 status
    .\scripts\gcp-sandbox-vm.ps1 ip

  Override defaults with environment variables: GCP_PROJECT, GCP_ZONE, GCP_INSTANCE
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'ip')]
    [string] $Action = 'status'
)

$Project = if ($env:GCP_PROJECT) { $env:GCP_PROJECT } else { 'adventure-pos-sandbox' }
$Zone = if ($env:GCP_ZONE) { $env:GCP_ZONE } else { 'us-central1-a' }
$Instance = if ($env:GCP_INSTANCE) { $env:GCP_INSTANCE } else { 'adventurepos-sandbox-vm' }

switch ($Action) {
    'start' {
        gcloud compute instances start $Instance --zone=$Zone --project=$Project
    }
    'stop' {
        gcloud compute instances stop $Instance --zone=$Zone --project=$Project
    }
    'status' {
        gcloud compute instances describe $Instance --zone=$Zone --project=$Project --format="value(status)"
    }
    'ip' {
        gcloud compute instances describe $Instance --zone=$Zone --project=$Project --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
    }
}
