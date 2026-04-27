#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ASSUME_YES="${1:-}"

if [[ "$ASSUME_YES" != "--yes" ]]; then
  cat <<'EOF'
This will permanently delete the local Docker Compose Postgres volume for this repo,
restart the stack, and reinitialize the default Odoo database.

Use this only for disposable dev data.
EOF
  printf "Type 'reset' to continue: "
  read -r confirmation
  if [[ "$confirmation" != "reset" ]]; then
    echo "Cancelled."
    exit 1
  fi
fi

echo "Stopping services and removing the local database volume..."
docker compose down --volumes --remove-orphans

echo "Starting services..."
docker compose up -d

echo "Initializing fresh Odoo database..."
bash ./scripts/odoo-init-db.sh

echo "Database reset complete."
