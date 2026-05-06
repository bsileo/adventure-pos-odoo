# Development Seed Data

AdventurePOS seed data is explicit dev tooling, not Odoo demo data. The seed runner is intended for local and disposable development databases, and for future automated system tests that need deterministic records.

## Profiles

The first supported profile is `dive_shop`, owned by the `dive_shop_pos` vertical module.

It creates:

- A stable dive shop company.
- Rental and fee products.
- Scuba rental package templates.
- Physical rental assets with representative states.
- Customers with certification and waiver scenarios.
- Reservations for pickup, return, overdue, and damaged-return workflows.
- Condition logs and maintenance events.

## Usage

PowerShell:

```powershell
.\scripts\seed-dev-db.ps1 -Profile dive_shop
.\scripts\seed-dev-db.ps1 -Profile dive_shop -ResetSeed
```

Bash:

```bash
bash ./scripts/seed-dev-db.sh --profile dive_shop
bash ./scripts/seed-dev-db.sh --profile dive_shop --reset-seed
```

The runner installs or updates `dive_shop_pos` before loading the seed profile.

## Idempotency

Seeded records are owned by stable XML IDs under the `dive_shop_pos_seed` namespace. Re-running the seed updates existing records instead of duplicating them.

`--reset-seed` deletes scenario/runtime records owned by that namespace, then recreates them. Stable catalog records such as products, categories, customers, and the company are updated in place so the reset can run safely while POS sessions exist. It does not wipe the database or remove non-seed records.
