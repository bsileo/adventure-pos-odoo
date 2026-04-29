#!/usr/bin/env bash
# Initialize the default Odoo database once if core tables are missing.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is not available. Start Docker and ensure the compose plugin is installed." >&2
  exit 1
fi

if [ -z "$(docker compose ps -q db 2>/dev/null)" ]; then
  echo "The Postgres (db) container is not running." >&2
  echo "From the repo root:  docker compose up -d" >&2
  exit 1
fi

# pg_isready checks the server is accepting connections (no password; avoids .env CRLF issues with psql).
# Cold start on Docker Desktop + bind mounts (e.g. WSL on /mnt/c) can take well over 60s.
wait_for_postgres() {
  local attempt max_attempts=90 sleep_seconds=2
  for attempt in $(seq 1 "${max_attempts}"); do
    if docker compose exec -T db sh -lc 'pg_isready -U "${POSTGRES_USER}" -d postgres' >/dev/null 2>&1; then
      return 0
    fi
    sleep "${sleep_seconds}"
  done

  echo "Postgres did not become ready in time (${max_attempts} attempts, ${sleep_seconds}s apart)." >&2
  echo "--- docker compose ps ---" >&2
  docker compose ps 2>&1 | sed 's/^/  /' || true
  echo "--- last db log lines (hint: first boot can be slow; ensure .env has POSTGRES_PASSWORD, Unix LF) ---" >&2
  docker compose logs --tail=40 db 2>&1 | sed 's/^/  /' || true
  echo "--- pg_isready (if this fails, Postgres is still starting or misconfigured) ---" >&2
  docker compose exec -T db sh -lc 'pg_isready -U "${POSTGRES_USER}" -d postgres' 2>&1 | sed 's/^/  /' || true
  exit 1
}

database_initialized() {
  docker compose exec -T db sh -lc 'PGPASSWORD="${POSTGRES_PASSWORD}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB:-odoo}" -tAc "SELECT 1 FROM information_schema.tables WHERE table_schema = '\''public'\'' AND table_name = '\''ir_module_module'\''" | grep -q 1' >/dev/null 2>&1
}

initialize_database() {
  docker compose exec odoo sh -lc 'db_user="${POSTGRES_USER:-$USER}"; db_password="${POSTGRES_PASSWORD:-$PASSWORD}"; db_name="${POSTGRES_DB:-odoo}"; odoo --db_host=db --db_port=5432 --db_user="$db_user" --db_password="$db_password" -d "$db_name" -i base --stop-after-init'
}

wait_for_postgres

if database_initialized; then
  echo "Odoo database already initialized."
else
  echo "Initializing Odoo database..."
  initialize_database
fi
