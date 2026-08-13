#!/usr/bin/env bash
# Run Odoo module tests inside the Compose odoo service.
#
# Per-module only (no default "run everything" tag set):
#   make test TEST_TAGS=/adventure_equipment
#   bash ./scripts/dev-test.sh --tags /adventure_equipment
#   bash ./scripts/dev-test.sh --modules adventure_equipment
#       (installs the module if needed and sets --test-tags=/adventure_equipment)
#
# Multiple modules when intentionally testing a small set:
#   bash ./scripts/dev-test.sh --tags /adventure_waiver,/adventure_smartwaiver
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

TAGS=""
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
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

# Derive tags from modules when tags were not given (one tag per module name).
if [[ -z "$TAGS" && -n "$MODULES" ]]; then
  TAGS=""
  IFS=',' read -r -a mod_array <<< "$MODULES"
  for mod in "${mod_array[@]}"; do
    mod="$(echo "$mod" | tr -d '[:space:]')"
    [[ -z "$mod" ]] && continue
    if [[ -n "$TAGS" ]]; then
      TAGS="${TAGS},/${mod}"
    else
      TAGS="/${mod}"
    fi
  done
fi

if [[ -z "$TAGS" ]]; then
  cat <<'EOF' >&2
dev-test.sh: per-module tests only — pass --tags or --modules (or make test TEST_TAGS=/module_name).

Examples:
  make test TEST_TAGS=/adventure_equipment
  bash ./scripts/dev-test.sh --tags /adventure_equipment_service
  bash ./scripts/dev-test.sh --modules adventure_waiver
EOF
  exit 2
fi

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
    "odoo --db_host=\"\${ODOO_DB_HOST:-\${HOST:-db}}\" --db_port=5432 --db_user=\"\${POSTGRES_USER}\" --db_password=\"\${POSTGRES_PASSWORD}\" -d \"\${POSTGRES_DB:-odoo}\" -i ${MODULES} --http-port=8070 --stop-after-init"
fi

echo "Running Odoo tests with --test-tags=${TAGS}"
"${DOCKER[@]}" compose exec -T odoo sh -lc \
  "odoo --db_host=\"\${ODOO_DB_HOST:-\${HOST:-db}}\" --db_port=5432 --db_user=\"\${POSTGRES_USER}\" --db_password=\"\${POSTGRES_PASSWORD}\" -d \"\${POSTGRES_DB:-odoo}\" --test-enable --http-port=8070 --stop-after-init --test-tags=${TAGS}"

echo "Tests finished."
