#!/usr/bin/env bash
# Ensure a local .env exists for Compose. Never commits secrets.
# Optional Cursor Cloud Secrets / env vars are merged when present:
#   OPENAI_API_KEY, SMARTWAIVER_API_KEY, POSTGRES_PASSWORD
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

EXAMPLE=".env.example"
TARGET=".env"

if [[ ! -f "$EXAMPLE" ]]; then
  echo "Missing $EXAMPLE" >&2
  exit 1
fi

if [[ ! -f "$TARGET" ]]; then
  cp "$EXAMPLE" "$TARGET"
  # Cloud / disposable VMs: unique volume name avoids colliding with shared sandbox naming.
  if [[ -n "${CURSOR_CLOUD:-}${CURSOR_AGENT:-}" ]] || [[ -n "${CLOUD_AGENT:-}" ]] || [[ "${DEV_ENV_PROFILE:-}" == "cursor-cloud" ]]; then
    if ! grep -q '^POSTGRES_VOLUME_NAME=' "$TARGET"; then
      printf '\nPOSTGRES_VOLUME_NAME=adventurepos-cloud-postgres\n' >>"$TARGET"
    fi
  fi
  echo "Created $TARGET from $EXAMPLE"
else
  echo "$TARGET already exists"
fi

# Merge optional secrets from the environment without printing values.
set_or_replace_env() {
  local key="$1"
  local value="$2"
  if [[ -z "$value" ]]; then
    return 0
  fi
  if grep -q "^${key}=" "$TARGET"; then
    # Replace in place without echoing the secret.
    local tmp
    tmp="$(mktemp)"
    awk -v k="$key" -v v="$value" 'BEGIN{FS=OFS="="} $1==k{$0=k"="v} {print}' "$TARGET" >"$tmp"
    mv "$tmp" "$TARGET"
  else
    printf '%s=%s\n' "$key" "$value" >>"$TARGET"
  fi
  echo "Applied $key from environment (value not printed)."
}

set_or_replace_env "OPENAI_API_KEY" "${OPENAI_API_KEY:-}"
set_or_replace_env "SMARTWAIVER_API_KEY" "${SMARTWAIVER_API_KEY:-}"
set_or_replace_env "POSTGRES_PASSWORD" "${POSTGRES_PASSWORD:-}"
