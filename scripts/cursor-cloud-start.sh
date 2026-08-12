#!/usr/bin/env bash
# Cursor cloud `start` hook: bring up Odoo/Postgres, ensure Tidewater DB, stay attached.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export DEV_ENV_PROFILE="${DEV_ENV_PROFILE:-cursor-cloud}"

# Full idempotent bootstrap then attach to logs so the start process stays alive.
bash ./scripts/dev-setup.sh
exec bash ./scripts/dev-start.sh --attach
