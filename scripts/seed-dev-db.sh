#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

profile="dive_shop"
reset_seed=0

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
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$profile" != "dive_shop" ]]; then
  echo "Unsupported seed profile: $profile" >&2
  exit 2
fi

docker compose exec -T odoo sh -lc 'odoo --db_host=db --db_port=5432 --db_user="${POSTGRES_USER}" --db_password="${POSTGRES_PASSWORD}" -d "${POSTGRES_DB:-odoo}" -i dive_shop_pos --stop-after-init >/tmp/dive_shop_pos_install.log'

docker compose exec -T odoo sh -lc 'odoo shell --db_host=db --db_port=5432 --db_user="${POSTGRES_USER}" --db_password="${POSTGRES_PASSWORD}" -d "${POSTGRES_DB:-odoo}"' <<PY
from odoo.addons.dive_shop_pos.seeds.run_seed import main
args = ["--profile", "$profile"]
if $reset_seed:
    args.append("--reset-seed")
stats = main(env, args)
env.cr.commit()
print("AdventurePOS seed complete: %s" % stats)
PY
