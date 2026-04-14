# Create or update GitHub labels for Adventure POS. Requires: gh auth login
# Usage: .\scripts\sync-github-labels.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

function Upsert-Label {
    param([string]$Name, [string]$Color, [string]$Description = '')
    gh label create $Name --color $Color --description $Description 2>$null
    if ($LASTEXITCODE -ne 0) {
        gh label edit $Name --color $Color --description $Description
    }
}

Upsert-Label 'type:chore' 'C5DEF5' 'Tooling, docs-only, or internal refactor'
Upsert-Label 'risk:db-migration' 'B60205' 'Schema/data migration—test upgrades carefully'
Upsert-Label 'agent:ready' '0E7490' 'Spec complete enough for an AI agent to implement'

Upsert-Label 'module:adventure_base' '0E8A16' 'addons/adventure_base'
Upsert-Label 'module:adventure_pos' '5319E7' 'addons/adventure_pos'
Upsert-Label 'module:adventure_inventory' 'FBCA04' 'addons/adventure_inventory'
Upsert-Label 'module:adventure_customers' 'D4C5F9' 'addons/adventure_customers'
Upsert-Label 'module:adventure_purchase' 'F9D0C4' 'addons/adventure_purchase'
Upsert-Label 'module:adventure_reports' 'C2E0C6' 'addons/adventure_reports'

Write-Host 'Labels synced. Default templates use GitHub''s built-in bug / enhancement labels.'
