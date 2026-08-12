# Development Seed Data

AdventurePOS seed data is explicit dev tooling, not Odoo demo data. The seed runner is intended for local and disposable development databases, the shared GCP sandbox, and future automated system tests that need deterministic records.

## Tidewater Dive Shop (sandbox-diveshop)

The canonical example tenant is **Tidewater Dive Shop** — a fictional Pittsburgh, PA dive shop used for demos, QA, and sandbox walkthroughs.

| Field | Value |
|-------|--------|
| Display name | Tidewater Dive Shop |
| Tenant slug | `shop_tidewater` |
| Seed profile | `tidewater` (`tideledger` and `dive_shop` are legacy aliases) |
| Location | Pittsburgh, PA |
| Contact | `ops@tidewater.example` / `+1 555-0412` |

**Sandbox role:** Tidewater is the **sandbox-diveshop** story tenant — open the shared GCP sandbox and expect a working dive shop, not an empty company.

Identity constants live in [`addons/dive_shop_pos/seeds/tidewater_identity.py`](../addons/dive_shop_pos/seeds/tidewater_identity.py).

**Agent rule:** when shipping new modules or user-visible functionality, add or extend a **module-owned Tidewater contributor** (linked to shared Tidewater identity) so the feature is testable and demonstrable after seed. See [agent-rules.md — Tidewater demo seed](agent-rules.md#tidewater-demo-seed-mandatory-for-features) and [Tidewater demo seed architecture](architecture/tidewater-demo-seed.md).

## Architecture (module-owned contributors)

Tidewater seed is **not** a single dump owned forever by one vertical pack.

- **Central:** company identity, shared XML-id conventions, story anchors others link to.
- **Per module:** demo rows for that module’s models (rentals, waivers, future domains, …), registered with the seed orchestrator.
- **Orchestrator:** `seed-tidewater` / sandbox bootstrap runs installed contributors in order; skips modules that are not installed.
- **Lifecycle:** deploys ship code only; reseed or sandbox reset loads data; re-run seed after installing a new module onto an existing Tidewater DB.

Full pattern, ownership table, and ongoing checklist: [architecture/tidewater-demo-seed.md](architecture/tidewater-demo-seed.md).

## Profiles

The supported profile is `tidewater` (aliases: `tideledger`, `dive_shop`), owned by the `dive_shop_pos` vertical module.

It creates / updates:

- Rebrands the database **main company** as Tidewater Dive Shop (Pittsburgh). It does **not** create a second company.
- Sets the Tidewater company logo (`dive_shop_pos/static/img/tidewater_logo.png`) used on the main login and POS login screens.
- A **Tidewater Front Desk** `pos.config` plus bank payment method (needed when Odoo demo data is off).
- Rental and fee products.
- Scuba rental package templates.
- Physical rental assets with representative states.
- Customers with certification and waiver scenarios.
- Reservations for pickup, return, overdue, and damaged-return workflows.
- Condition logs and maintenance events.
- **Customer-owned equipment** (when `adventure_equipment_scuba` is installed): kit and service history for Tidewater story customers (Maya Carter, Jon Ellis, Luis Romero, Nora Singh, Carter Family), via the module-owned contributor under `adventure_equipment_scuba/seeds/`.

### Tidewater standard package modules

`seed-tidewater` / sandbox bootstrap installs (when missing):

| Module | Role |
|--------|------|
| `dive_shop_pos` | Scuba POS / rental vertical + central seed orchestrator |
| `adventure_equipment_scuba` | Customer equipment scuba app (pulls `adventure_equipment` + `adventure_equipment_service`) |

`adventure_equipment` is an Odoo **App** (`application=True`). `adventure_equipment_scuba` is also an **App**. `adventure_equipment_service` remains a supporting module (`application=False`) so it does not appear when filtering Apps alone—install it via the scuba app or Apps → Modules.

## Usage (local / Cursor cloud)

Preferred full bootstrap (Docker, init DB, Tidewater):

```bash
make setup
# wipe disposable local/cloud DB and reseed:
make reset ASSUME_YES=1
```

PowerShell (seed only):

```powershell
.\scripts\seed-dev-db.ps1
.\scripts\seed-dev-db.ps1 -Profile tidewater -ResetSeed
```

Bash / Make (seed only):

```bash
bash ./scripts/seed-dev-db.sh --profile tidewater
bash ./scripts/seed-dev-db.sh --profile tidewater --reset-seed
make seed-tidewater
make seed-tidewater RESET_SEED=1
```

The runner installs or updates the Tidewater standard package (`dive_shop_pos`, `adventure_equipment_scuba`) before loading the seed profile.

**Do not** restore repo-root `backup.sql` for development — it is not the supported dataset.

## Sandbox

Normal **`develop` deploys do not reseed** — they ship code only and leave live sandbox data alone.

| Goal | Command |
|------|---------|
| Refresh Tidewater without wiping the DB | `bash ./scripts/gcp-sandbox-seed-tidewater.sh` (optional `--reset-seed`) |
| Wipe sandbox DB and bootstrap Tidewater | `bash ./scripts/gcp-sandbox-reset-db.sh` |
| Wipe only (no seed) | `bash ./scripts/gcp-sandbox-reset-db.sh --skip-seed` |

From Windows against the VM (set `GCP_SANDBOX_SSH_HOST`):

```powershell
.\scripts\gcp-sandbox-seed-tidewater.ps1
.\scripts\gcp-sandbox-seed-tidewater.ps1 -ResetSeed
.\scripts\gcp-sandbox-reset-db.ps1
```

See [shared-environment.md](shared-environment.md) for VM access and reset details.

## Idempotency

Seeded records are owned by stable XML IDs under the `dive_shop_pos_seed` namespace. Re-running the seed updates existing records instead of duplicating them.

`--reset-seed` deletes scenario/runtime records owned by that namespace, then recreates them. Stable catalog records such as products, categories, customers, and the company are updated in place so the reset can run safely while POS sessions exist. It does not wipe the database or remove non-seed records.
