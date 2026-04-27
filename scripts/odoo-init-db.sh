#!/usr/bin/env bash
# Initialize the default Odoo database once if core tables are missing.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

wait_for_postgres() {
  local attempt
  for attempt in $(seq 1 30); do
    if docker compose exec -T db sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1"' >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "Postgres did not become ready in time." >&2
  exit 1
}

database_initialized() {
  docker compose exec -T db sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "${POSTGRES_DB:-odoo}" -tAc "SELECT 1 FROM information_schema.tables WHERE table_schema = '\''public'\'' AND table_name = '\''ir_module_module'\''" | grep -q 1' >/dev/null 2>&1
}

initialize_database() {
  # --without-demo=all skips Odoo sample/demonstration data (shared sandbox and local init-db).
  docker compose exec odoo sh -lc 'db_user="${POSTGRES_USER:-$USER}"; db_password="${POSTGRES_PASSWORD:-$PASSWORD}"; db_name="${POSTGRES_DB:-odoo}"; odoo --db_host=db --db_port=5432 --db_user="$db_user" --db_password="$db_password" -d "$db_name" -i base --without-demo=all --stop-after-init'
}

wait_for_postgres

if database_initialized; then
  echo "Odoo database already initialized."
else
  echo "Initializing Odoo database..."
  initialize_database
fi
