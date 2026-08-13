#!/usr/bin/env bash
# Cursor cloud `install` hook: terminate after deps / images are ready.
# Does not run long-lived servers. DB init + Tidewater seed happen on start/setup.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export DEV_ENV_PROFILE="${DEV_ENV_PROFILE:-cursor-cloud}"

bash ./scripts/ensure-docker.sh
bash ./scripts/ensure-dotenv.sh

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo docker)
fi

# Pull/build images so agent sessions start faster.
"${DOCKER[@]}" compose pull db || true
"${DOCKER[@]}" compose build

# Docs toolchain (optional; used for mkdocs checks).
if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --user -q -r requirements-docs.txt || true
fi

echo "Cursor cloud install complete."
