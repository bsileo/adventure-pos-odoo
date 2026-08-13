#!/usr/bin/env bash
# Load or refresh Tidewater seed data on the shared GCP sandbox.
#
# Run ON the sandbox VM as `deploy`, from the repo root — e.g.:
#   cd /srv/adventurepos/adventure-pos-odoo
#   bash ./scripts/gcp-sandbox-seed-tidewater.sh
#   bash ./scripts/gcp-sandbox-seed-tidewater.sh --reset-seed
#
# From your PC, use gcp-sandbox-seed-tidewater.ps1 instead.
#
# This does NOT wipe the Postgres volume. It installs the Tidewater standard
# package (dive_shop_pos + equipment scuba + website/portal and dependencies)
# if needed and upserts Tidewater seed records. Use --reset-seed to recreate
# scenario records (reservations, assets, customer equipment, etc.) while keeping
# stable products/customers.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

reset_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --reset-seed)
      reset_args+=(--reset-seed)
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: gcp-sandbox-seed-tidewater.sh [--reset-seed]

Seeds Tidewater Dive Shop (sandbox-diveshop) into the current sandbox database.
Does not wipe Postgres. Prefer this for day-to-day demo refresh.

For a full empty DB + Tidewater bootstrap, use gcp-sandbox-reset-db.sh instead.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

echo "Seeding Tidewater Dive Shop on sandbox..."
bash "$ROOT_DIR/scripts/seed-dev-db.sh" --profile tidewater "${reset_args[@]+"${reset_args[@]}"}"
echo "Sandbox Tidewater seed complete."
