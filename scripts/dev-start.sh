#!/usr/bin/env bash
# Start (or ensure) the development stack. Idempotent.
# Usage:
#   bash ./scripts/dev-start.sh           # detached (default)
#   bash ./scripts/dev-start.sh --attach  # follow logs (for Cursor cloud start)
#   bash ./scripts/dev-start.sh --setup   # also init-db + seed if needed
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ATTACH=0
RUN_SETUP=0
for arg in "$@"; do
  case "$arg" in
    --attach) ATTACH=1 ;;
    --setup) RUN_SETUP=1 ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

bash ./scripts/ensure-docker.sh
bash ./scripts/ensure-dotenv.sh

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo docker)
fi

"${DOCKER[@]}" compose up -d

if [[ "$RUN_SETUP" -eq 1 ]]; then
  bash ./scripts/odoo-init-db.sh
  # Seed is idempotent; safe to re-run so modules/data catch up after pulls.
  bash ./scripts/seed-dev-db.sh --profile tidewater
fi

echo "Stack is up. Odoo: http://127.0.0.1:8069"
"${DOCKER[@]}" compose ps

if [[ "$ATTACH" -eq 1 ]]; then
  echo "Attaching to compose logs (Ctrl-C stops follow only if you interrupt; containers keep running if started with -d)."
  exec "${DOCKER[@]}" compose logs -f
fi
