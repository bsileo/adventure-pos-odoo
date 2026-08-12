#!/usr/bin/env bash
# Install the Tidewater Dive Shop standard package (if needed) and load the
# Tidewater seed profile. Safe to re-run; use --reset-seed to recreate
# scenario/runtime seed records.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

profile="tidewater"
reset_seed=0

# Standard Tidewater package: dive vertical + customer equipment scuba stack.
# adventure_equipment_scuba pulls adventure_equipment_service + adventure_equipment.
TIDEWATER_MODULES="dive_shop_pos,adventure_equipment_scuba"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      profile="${2:?Missing value for --profile}"
      shift 2
      ;;
    --reset-seed)
      reset_seed=1
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: seed-dev-db.sh [--profile tidewater|tideledger|dive_shop] [--reset-seed]

Canonical profile is tidewater (Tidewater Dive Shop, Pittsburgh).
tideledger and dive_shop remain as legacy aliases for the same seed pack.

Installs the Tidewater standard package modules when missing:
  dive_shop_pos, adventure_equipment_scuba
(and their dependencies, including adventure_equipment / adventure_equipment_service).
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$profile" != "tidewater" && "$profile" != "tideledger" && "$profile" != "dive_shop" ]]; then
  echo "Unsupported seed profile: $profile" >&2
  exit 2
fi

echo "Ensuring Tidewater standard package is installed (${TIDEWATER_MODULES})..."
docker compose exec -T odoo sh -lc "odoo --db_host=\"\${ODOO_DB_HOST:-\${HOST:-db}}\" --db_port=5432 --db_user=\"\${POSTGRES_USER}\" --db_password=\"\${POSTGRES_PASSWORD}\" -d \"\${POSTGRES_DB:-odoo}\" -i ${TIDEWATER_MODULES} --stop-after-init >/tmp/tidewater_package_install.log"

echo "Loading Tidewater seed profile (${profile})..."
docker compose exec -T odoo sh -lc 'odoo shell --db_host="${ODOO_DB_HOST:-${HOST:-db}}" --db_port=5432 --db_user="${POSTGRES_USER}" --db_password="${POSTGRES_PASSWORD}" -d "${POSTGRES_DB:-odoo}"' <<PY
from odoo.addons.dive_shop_pos.seeds.run_seed import main
args = ["--profile", "$profile"]
if $reset_seed:
    args.append("--reset-seed")
stats = main(env, args)
env.cr.commit()
print("AdventurePOS seed complete: %s" % stats)
PY
