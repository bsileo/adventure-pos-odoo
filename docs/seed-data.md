# Development Seed Data

AdventurePOS seed data is explicit dev tooling, not Odoo demo data. The seed runner is intended for local and disposable development databases, the shared GCP sandbox, and future automated system tests that need deterministic records.

## Tideledger Dive Co. (sandbox-diveshop)

The canonical example tenant is **Tideledger Dive Co.** — a fictional Pittsburgh, PA dive shop used for demos, QA, and sandbox walkthroughs.

| Field | Value |
|-------|--------|
| Display name | Tideledger Dive Co. |
| Tenant slug | `shop_tideledger` |
| Seed profile | `tideledger` (`dive_shop` is a legacy alias) |
| Location | Pittsburgh, PA |
| Contact | `ops@tideledger.example` / `+1 555-0412` |

**Sandbox role:** Tideledger is the **sandbox-diveshop** story tenant — open the shared GCP sandbox and expect a working dive shop, not an empty company.

Identity constants live in [`addons/dive_shop_pos/seeds/tideledger_identity.py`](../addons/dive_shop_pos/seeds/tideledger_identity.py).

## Profiles

The supported profile is `tideledger` (alias: `dive_shop`), owned by the `dive_shop_pos` vertical module.

It creates:

- The Tideledger company (Pittsburgh).
- Rental and fee products.
- Scuba rental package templates.
- Physical rental assets with representative states.
- Customers with certification and waiver scenarios.
- Reservations for pickup, return, overdue, and damaged-return workflows.
- Condition logs and maintenance events.

## Usage (local)

PowerShell:

```powershell
.\scripts\seed-dev-db.ps1
.\scripts\seed-dev-db.ps1 -Profile tideledger -ResetSeed
```

Bash / Make:

```bash
bash ./scripts/seed-dev-db.sh --profile tideledger
bash ./scripts/seed-dev-db.sh --profile tideledger --reset-seed
make seed-tideledger
make seed-tideledger RESET_SEED=1
```

The runner installs or updates `dive_shop_pos` before loading the seed profile.

## Sandbox

Normal **`develop` deploys do not reseed** — they ship code only and leave live sandbox data alone.

| Goal | Command |
|------|---------|
| Refresh Tideledger without wiping the DB | `bash ./scripts/gcp-sandbox-seed-tideledger.sh` (optional `--reset-seed`) |
| Wipe sandbox DB and bootstrap Tideledger | `bash ./scripts/gcp-sandbox-reset-db.sh` |
| Wipe only (no seed) | `bash ./scripts/gcp-sandbox-reset-db.sh --skip-seed` |

From Windows against the VM (set `GCP_SANDBOX_SSH_HOST`):

```powershell
.\scripts\gcp-sandbox-seed-tideledger.ps1
.\scripts\gcp-sandbox-seed-tideledger.ps1 -ResetSeed
.\scripts\gcp-sandbox-reset-db.ps1
```

See [shared-environment.md](shared-environment.md) for VM access and reset details.

## Idempotency

Seeded records are owned by stable XML IDs under the `dive_shop_pos_seed` namespace. Re-running the seed updates existing records instead of duplicating them.

`--reset-seed` deletes scenario/runtime records owned by that namespace, then recreates them. Stable catalog records such as products, categories, customers, and the company are updated in place so the reset can run safely while POS sessions exist. It does not wipe the database or remove non-seed records.
