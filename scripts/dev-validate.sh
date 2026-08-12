#!/usr/bin/env bash
# Smoke validation for the Tidewater development database.
# Checks (API-level; agents should also use the browser for UI review):
#   A) Authenticate as admin and confirm company branding is Tidewater Dive Shop
#   C) Confirm at least one POS config exists and the POS UI URL responds
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ODOO_URL="${ODOO_URL:-http://127.0.0.1:8069}"
ODOO_DB="${ODOO_DB:-odoo}"
ODOO_LOGIN="${ODOO_LOGIN:-admin}"
ODOO_PASSWORD="${ODOO_PASSWORD:-admin}"

bash ./scripts/ensure-docker.sh

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo docker)
fi

"${DOCKER[@]}" compose up -d >/dev/null

wait_http() {
  local attempt
  for attempt in $(seq 1 60); do
    if curl -fsS "$ODOO_URL/web/login" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Odoo HTTP did not become ready at $ODOO_URL" >&2
  "${DOCKER[@]}" compose ps >&2 || true
  "${DOCKER[@]}" compose logs --tail=40 odoo >&2 || true
  exit 1
}

echo "Waiting for Odoo at $ODOO_URL ..."
wait_http

python3 - "$ODOO_URL" "$ODOO_DB" "$ODOO_LOGIN" "$ODOO_PASSWORD" <<'PY'
import json
import sys
import urllib.error
import urllib.request
import xmlrpc.client

url, db, login, password = sys.argv[1:5]

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

print(f"A) Authenticating as {login!r} on database {db!r}...")
uid = common.authenticate(db, login, password, {})
if not uid:
    raise SystemExit("Login failed (expected disposable admin/admin after init-db unless overridden).")

company_ids = models.execute_kw(
    db, uid, password, "res.company", "search", [[]], {"limit": 5}
)
companies = models.execute_kw(
    db, uid, password, "res.company", "read", [company_ids], {"fields": ["name"]}
)
names = [c["name"] for c in companies]
print("   Companies:", ", ".join(names) or "(none)")
if not any("Tidewater" in (n or "") for n in names):
    raise SystemExit(
        "Tidewater Dive Shop company not found. Run: make setup  (or make seed-tidewater)"
    )
print("   OK: Tidewater company present.")

print("C) Checking Point of Sale configuration...")
pos_ids = models.execute_kw(db, uid, password, "pos.config", "search", [[]], {"limit": 10})
if not pos_ids:
    raise SystemExit(
        "No pos.config records found. Install/seed Tidewater package (dive_shop_pos pulls point_of_sale)."
    )
pos_rows = models.execute_kw(
    db, uid, password, "pos.config", "read", [pos_ids], {"fields": ["name", "id"]}
)
for row in pos_rows:
    print(f"   POS config: {row['name']!r} (id={row['id']})")

config_id = pos_ids[0]
pos_ui = f"{url}/pos/ui?config_id={config_id}"
req = urllib.request.Request(pos_ui, method="GET")
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = resp.status
        body = resp.read(200)
except urllib.error.HTTPError as exc:
    # Odoo may redirect unauthenticated POS UI to login (302/303) or 303 — treat as reachable.
    status = exc.code
    body = exc.read(200) if exc.fp else b""
except urllib.error.URLError as exc:
    raise SystemExit(f"POS UI unreachable: {exc}") from exc

print(f"   POS UI probe {pos_ui} → HTTP {status}")
if status >= 500:
    raise SystemExit("POS UI returned server error.")
print("   OK: POS config exists and UI endpoint responds.")

print(json.dumps({"ok": True, "uid": uid, "companies": names, "pos_configs": pos_rows}, indent=2))
print("Validation passed (A + C). For human review, keep the stack up and open the browser.")
PY
