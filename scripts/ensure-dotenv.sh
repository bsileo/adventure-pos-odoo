#!/usr/bin/env bash
# Ensure a local .env exists for Compose. Never commits secrets.
# Optional Cursor Cloud Secrets / env vars are merged when present:
#   OPENAI_API_KEY, SMARTWAIVER_API_KEY, POSTGRES_PASSWORD
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

EXAMPLE=".env.example"
TARGET=".env"

is_cursor_cloud() {
  [[ -n "${CURSOR_CLOUD:-}${CURSOR_AGENT:-}${CLOUD_AGENT:-}" ]] \
    || [[ "${DEV_ENV_PROFILE:-}" == "cursor-cloud" ]] \
    || [[ -f /.dockerenv && "$(findmnt -no FSTYPE / 2>/dev/null || true)" == "overlay" ]]
}

if [[ ! -f "$EXAMPLE" ]]; then
  echo "Missing $EXAMPLE" >&2
  exit 1
fi

if [[ ! -f "$TARGET" ]]; then
  cp "$EXAMPLE" "$TARGET"
  echo "Created $TARGET from $EXAMPLE"
else
  echo "$TARGET already exists"
fi

set_or_replace_env() {
  local key="$1"
  local value="$2"
  if [[ -z "$value" ]]; then
    return 0
  fi
  if grep -q "^${key}=" "$TARGET"; then
    local tmp
    tmp="$(mktemp)"
    awk -v k="$key" -v v="$value" 'BEGIN{FS=OFS="="} $1==k{$0=k"="v} {print}' "$TARGET" >"$tmp"
    mv "$tmp" "$TARGET"
  else
    printf '%s=%s\n' "$key" "$value" >>"$TARGET"
  fi
  echo "Applied $key from environment (value not printed)."
}

# Cloud / nested overlay hosts: host-network compose + isolated volume + loopback DB host.
if is_cursor_cloud; then
  export DEV_ENV_PROFILE="${DEV_ENV_PROFILE:-cursor-cloud}"
  if ! grep -q '^POSTGRES_VOLUME_NAME=' "$TARGET"; then
    set_or_replace_env "POSTGRES_VOLUME_NAME" "${POSTGRES_VOLUME_NAME:-adventurepos-cloud-postgres}"
  fi
  if ! grep -q '^COMPOSE_FILE=' "$TARGET"; then
    set_or_replace_env "COMPOSE_FILE" "${COMPOSE_FILE:-docker-compose.cloud.yml}"
  fi
  if ! grep -q '^ODOO_DB_HOST=' "$TARGET"; then
    set_or_replace_env "ODOO_DB_HOST" "${ODOO_DB_HOST:-127.0.0.1}"
  fi
fi

set_or_replace_env "OPENAI_API_KEY" "${OPENAI_API_KEY:-}"
set_or_replace_env "SMARTWAIVER_API_KEY" "${SMARTWAIVER_API_KEY:-}"
set_or_replace_env "POSTGRES_PASSWORD" "${POSTGRES_PASSWORD:-}"
