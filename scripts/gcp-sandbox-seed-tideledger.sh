#!/usr/bin/env bash
# Load or refresh Tideledger seed data on the shared GCP sandbox.
#
# Run ON the sandbox VM as `deploy`, from the repo root — e.g.:
#   cd /srv/adventurepos/adventure-pos-odoo
#   bash ./scripts/gcp-sandbox-seed-tideledger.sh
#   bash ./scripts/gcp-sandbox-seed-tideledger.sh --reset-seed
#
# From your PC, use gcp-sandbox-seed-tideledger.ps1 instead.
#
# This does NOT wipe the Postgres volume. It installs dive_shop_pos if needed
# and upserts Tideledger seed records. Use --reset-seed to recreate scenario
# records (reservations, assets, etc.) while keeping stable products/customers.
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
Usage: gcp-sandbox-seed-tideledger.sh [--reset-seed]

Seeds Tideledger Dive Co. (sandbox-diveshop) into the current sandbox database.
Does not wipe Postgres. Prefer this for day-to-day demo refresh.

For a full empty DB + Tideledger bootstrap, use gcp-sandbox-reset-db.sh instead.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

echo "Seeding Tideledger Dive Co. on sandbox..."
bash "$ROOT_DIR/scripts/seed-dev-db.sh" --profile tideledger "${reset_args[@]+"${reset_args[@]}"}"
echo "Sandbox Tideledger seed complete."
