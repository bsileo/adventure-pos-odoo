#Requires -Version 5.1
# One-shot Odoo DB init (installs "base" if the DB is empty) — same as: make init-db
#
# Use this on Windows when "make" and WSL "make" are not ideal: it runs the real bash script
# in Git Bash, which uses the same Docker Desktop context as "docker compose" in PowerShell.
# If the stack was started in PowerShell, do NOT use WSL to run the .sh; use this script or Git Bash.
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$pfx86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
$bashCandidates = @(
    (Join-Path $env:ProgramFiles "Git\bin\bash.exe")
) + @(
    if ($pfx86) { Join-Path $pfx86 "Git\bin\bash.exe" }
) + @(
    "bash"
)
$bash = $null
foreach ($b in $bashCandidates) {
    if ($b -and (Test-Path -LiteralPath $b)) { $bash = (Resolve-Path $b).Path; break }
    if ($b -eq "bash" -and (Get-Command bash -ErrorAction SilentlyContinue)) { $bash = (Get-Command bash).Path; break }
}
if (-not $bash) {
    Write-Error "Git Bash (bash.exe) not found. Install Git for Windows, or in PowerShell run: docker compose exec -T db ... (see scripts/odoo-init-db.sh). Optional: add bash to PATH (e.g. scoop)."
    exit 1
}

$unixish = $RepoRoot -replace "\\", "/"
# Git Bash: /c/Users/... style; MSYS2_ARG_CONV_EXCL avoids path mangling
$env:MSYS2_ARG_CONV_EXCL = "*"
& $bash -lc "cd '$unixish' && ./scripts/odoo-init-db.sh"
exit $LASTEXITCODE
