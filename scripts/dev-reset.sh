#!/usr/bin/env bash
# Wipe local Compose Postgres volume, re-init Odoo, reload Tidewater seed.
# Disposable development data only — never use against production or the
# shared GCP sandbox unless an operator explicitly chooses those scripts.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ASSUME_YES=0
if [[ "${1:-}" == "--yes" ]] || [[ "${1:-}" == "-y" ]]; then
  ASSUME_YES=1
fi

if [[ "$ASSUME_YES" -ne 1 ]]; then
  cat <<'EOF'
This permanently deletes the local Docker Compose Postgres volume for this clone,
reinitializes Odoo, and reloads the Tidewater Dive Shop seed.

Use only for disposable local / Cursor cloud development databases.
EOF
  printf "Type 'reset' to continue: "
  read -r confirmation
  if [[ "$confirmation" != "reset" ]]; then
    echo "Cancelled."
    exit 1
  fi
fi

bash ./scripts/ensure-docker.sh
bash ./scripts/ensure-dotenv.sh

bash ./scripts/odoo-reset-db.sh --yes
bash ./scripts/seed-dev-db.sh --profile tidewater

echo "Development environment reset complete (Tidewater seeded)."
echo "Odoo: http://127.0.0.1:8069  Login: admin / admin"
