#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet("tidewater", "tideledger", "dive_shop")]
    [string]$Profile = "tidewater",
    [switch]$ResetSeed
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$python = @"
from odoo.addons.dive_shop_pos.seeds.run_seed import main
args = ["--profile", "$Profile"]
if "$($ResetSeed.IsPresent)".lower() == "true":
    args.append("--reset-seed")
stats = main(env, args)
env.cr.commit()
print("AdventurePOS seed complete: %s" % stats)
"@

Write-Host "Ensuring dive_shop_pos is installed..."
docker compose exec -T odoo sh -lc 'odoo --db_host=db --db_port=5432 --db_user="${POSTGRES_USER}" --db_password="${POSTGRES_PASSWORD}" -d "${POSTGRES_DB:-odoo}" -i dive_shop_pos --stop-after-init >/tmp/dive_shop_pos_install.log'

Write-Host "Loading Tidewater seed profile ($Profile)..."
$python | docker compose exec -T odoo sh -lc 'odoo shell --db_host=db --db_port=5432 --db_user="${POSTGRES_USER}" --db_password="${POSTGRES_PASSWORD}" -d "${POSTGRES_DB:-odoo}"'
