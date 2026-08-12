#!/usr/bin/env bash
# Run Odoo module tests inside the Compose odoo service.
#
# Usage:
#   bash ./scripts/dev-test.sh
#   bash ./scripts/dev-test.sh --tags /adventure_equipment,/adventure_waiver
#   bash ./scripts/dev-test.sh --modules adventure_equipment,adventure_equipment_service
#
# Default tags cover Adventure modules that currently ship tests.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

DEFAULT_TAGS="/adventure_equipment,/adventure_equipment_service,/adventure_equipment_scuba,/adventure_waiver,/adventure_smartwaiver,/adventure_d360_migration"
TAGS="$DEFAULT_TAGS"
MODULES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tags)
      TAGS="${2:?Missing value for --tags}"
      shift 2
      ;;
    --modules)
      MODULES="${2:?Missing value for --modules}"
      shift 2
      ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
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
bash ./scripts/odoo-init-db.sh

# Ensure modules under test are installed when explicitly requested.
if [[ -n "$MODULES" ]]; then
  echo "Installing/updating modules: $MODULES"
  "${DOCKER[@]}" compose exec -T odoo sh -lc \
    "odoo --db_host=db --db_port=5432 --db_user=\"\${POSTGRES_USER}\" --db_password=\"\${POSTGRES_PASSWORD}\" -d \"\${POSTGRES_DB:-odoo}\" -i ${MODULES} --stop-after-init"
fi

echo "Running Odoo tests with --test-tags=${TAGS}"
"${DOCKER[@]}" compose exec -T odoo sh -lc \
  "odoo --db_host=db --db_port=5432 --db_user=\"\${POSTGRES_USER}\" --db_password=\"\${POSTGRES_PASSWORD}\" -d \"\${POSTGRES_DB:-odoo}\" --test-enable --stop-after-init --test-tags=${TAGS}"

echo "Tests finished."
