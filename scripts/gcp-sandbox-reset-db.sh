#!/usr/bin/env bash
# Reset the shared GCP sandbox Odoo database (destructive).
#
# Run ON the sandbox VM as `deploy`, from the repo root — e.g.:
#   cd /srv/adventurepos/adventure-pos-odoo
#   bash ./scripts/gcp-sandbox-reset-db.sh
#
# From your PC (interactive SSH TTY), use gcp-sandbox-reset-db.ps1 instead.
#
# This removes the Docker Postgres volume, restarts the stack, and runs
# odoo-init-db.sh (base only, --without-demo=all). Same effect as
# odoo-reset-db.sh with an extra sandbox-specific confirmation.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ASSUME_YES="${1:-}"

if [[ "$ASSUME_YES" != "--yes" ]]; then
  cat <<'EOF'
================================================================================
WARNING — Shared GCP sandbox database reset
================================================================================

This will PERMANENTLY delete the Postgres Docker volume for this stack and
reinitialize an empty Odoo database (base module only, no demonstration data).

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

exec bash "$ROOT_DIR/scripts/odoo-reset-db.sh" --yes
