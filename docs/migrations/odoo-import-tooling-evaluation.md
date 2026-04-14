# Odoo import tooling evaluation (Adventure POS)

**Goal:** Prefer standard Odoo mechanisms before custom ETL. Pick defaults per object type and document for each migration.

## Options

| Mechanism | Best for | Pros | Cons |
|-----------|----------|------|------|
| **UI import** (`base_import` / Import menu) | One-off, smaller files, iterative mapping | No code; visible errors | Manual, slow for huge files |
| **CSV + RPC** `load()` / XML-RPC | Repeatable scripts, CI-like dry runs | Automatable | Needs dev auth, chunking |
| **`odoo shell`** one-off scripts in `scripts/` | Complex transforms in Python | Full ORM access | Must run in controlled env |
| **Odoo Studio** (if licensed) | Ad-hoc models / quick fields | Fast experiments | Not a substitute for versioned module code for core models |

## Recommended defaults (tune per engagement)

| Data type | Suggested path |
|-----------|----------------|
| Products / partners (medium size) | UI import or scripted `load()` |
| Large catalogs (100k+ rows) | Batched RPC or shell; profile memory |
| Stock opening | Inventory adjustment workflow or dedicated import **after** products exist — see [stock-opening-valuation-strategy.md](stock-opening-valuation-strategy.md) |
| Historical POS | Highest risk — see [historical-pos-import-spike.md](historical-pos-import-spike.md) |

## Checklist before any bulk load

- [ ] [chart-of-accounts-localization.md](chart-of-accounts-localization.md) baseline done
- [ ] Company, warehouse, stock locations exist
- [ ] [external-id-convention.md](external-id-convention.md) agreed for idempotency
- [ ] Test import on **copy** of DB first

## Recorded choice for this program

| Object | Chosen tooling | Notes / script path |
|--------|----------------|---------------------|
| | | |
