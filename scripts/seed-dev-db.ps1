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

# Standard Tidewater package: dive vertical + equipment scuba + website/portal.
$TidewaterModules = "dive_shop_pos,adventure_equipment_scuba,adventure_website,adventure_equipment_portal,adventure_equipment_configuration,adventure_equipment_configuration_portal"

$python = @"
from odoo.addons.dive_shop_pos.seeds.run_seed import main
args = ["--profile", "$Profile"]
if "$($ResetSeed.IsPresent)".lower() == "true":
    args.append("--reset-seed")
stats = main(env, args)
env.cr.commit()
print("AdventurePOS seed complete: %s" % stats)
"@

Write-Host "Ensuring Tidewater standard package is installed ($TidewaterModules)..."
docker compose exec -T odoo sh -lc "odoo --db_host=db --db_port=5432 --db_user=`"`${POSTGRES_USER}`" --db_password=`"`${POSTGRES_PASSWORD}`" -d `"`${POSTGRES_DB:-odoo}`" -i $TidewaterModules --stop-after-init >/tmp/tidewater_package_install.log"

Write-Host "Loading Tidewater seed profile ($Profile)..."
$python | docker compose exec -T odoo sh -lc 'odoo shell --db_host=db --db_port=5432 --db_user="${POSTGRES_USER}" --db_password="${POSTGRES_PASSWORD}" -d "${POSTGRES_DB:-odoo}"'
