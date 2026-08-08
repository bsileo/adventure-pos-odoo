#!/usr/bin/env bash
# Reset the shared GCP sandbox Odoo database (destructive).
#
# Run ON the sandbox VM as `deploy`, from the repo root — e.g.:
#   cd /srv/adventurepos/adventure-pos-odoo
#   bash ./scripts/gcp-sandbox-reset-db.sh
#
# From your PC (interactive SSH TTY), use gcp-sandbox-reset-db.ps1 instead.
#
# This removes the Docker Postgres volume, restarts the stack, runs
# odoo-init-db.sh (base only, --without-demo=all), then bootstraps the
# Tidewater Dive Shop seed pack so the sandbox comes back as a working shop.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ASSUME_YES=""
SKIP_SEED=0
for arg in "$@"; do
  case "$arg" in
    --yes) ASSUME_YES="--yes" ;;
    --skip-seed) SKIP_SEED=1 ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: gcp-sandbox-reset-db.sh [--yes] [--skip-seed]" >&2
      exit 2
      ;;
  esac
done

if [[ "$ASSUME_YES" != "--yes" ]]; then
  cat <<'EOF'
================================================================================
WARNING — Shared GCP sandbox database reset
================================================================================

This will PERMANENTLY delete the Postgres Docker volume for this stack and
reinitialize an empty Odoo database (base module only, no demonstration data),
then load the Tidewater Dive Shop seed (sandbox-diveshop) unless --skip-seed
is passed.

All Odoo data on this sandbox is lost for everyone: partners, products, POS,
transactions, installed-module state, filestore references in DB, etc.

Run this only on the team sandbox VM, in the deploy clone — never on production.

================================================================================
EOF
  printf "Type reset-sandbox to continue (anything else aborts): "
  read -r confirmation
  if [[ "$confirmation" != "reset-sandbox" ]]; then
    echo "Cancelled."
    exit 1
  fi
fi

# Older clones used the directory name as the Compose project (e.g. adventure-pos-odoo).
# compose.yml now sets `name: adventurepos`, so `docker compose down` alone does not
# stop those containers: Postgres stays on 127.0.0.1:5432 and the volume stays "in use".
echo "Stopping any leftover stack from project name adventure-pos-odoo..."
docker compose -p adventure-pos-odoo down --volumes --remove-orphans 2>/dev/null || true

bash "$ROOT_DIR/scripts/odoo-reset-db.sh" --yes

if [[ "$SKIP_SEED" -eq 1 ]]; then
  echo "Skipping Tidewater seed (--skip-seed)."
  exit 0
fi

echo "Bootstrapping Tidewater Dive Shop (sandbox-diveshop)..."
bash "$ROOT_DIR/scripts/gcp-sandbox-seed-tidewater.sh"
echo "Sandbox reset + Tidewater bootstrap complete."
