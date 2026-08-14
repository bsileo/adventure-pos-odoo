#!/usr/bin/env bash
# Idempotent development bootstrap (local + Cursor cloud):
#   Docker ready → .env → compose build/up → init-db → Tidewater seed
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export DEV_ENV_PROFILE="${DEV_ENV_PROFILE:-}"

bash ./scripts/ensure-docker.sh
bash ./scripts/ensure-dotenv.sh

echo "Building and starting Compose services..."
if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo docker)
fi

"${DOCKER[@]}" compose build
"${DOCKER[@]}" compose up -d

bash ./scripts/odoo-init-db.sh

echo "Loading Tidewater Dive Shop seed (canonical dive-shop development dataset)..."
bash ./scripts/seed-dev-db.sh --profile tidewater

echo
echo "Development environment is ready."
echo "  Odoo:  http://127.0.0.1:8069  (database: odoo)"
echo "  Login: admin / admin  (disposable local/cloud DB default; change if you set otherwise)"
echo "  Next:  make validate   # or: bash ./scripts/dev-validate.sh"
echo "         make test       # or: bash ./scripts/dev-test.sh"
echo "  Leave the stack running for human browser review when useful."
