# Idempotency test procedure

**Purpose:** Prove that re-running the same migration inputs does **not** create duplicate partners, products, or conflicting stock when using [external-id-convention.md](external-id-convention.md).

## Prerequisites

- Staging **copy** of DB **after** first successful import **or** empty DB (depending on test design).
- Same export bundle (checksum verified) as first run.

## Procedure

1. Record counts: partners, products, variants, stock quants (or equivalent) — match [validation-report-template.md](validation-report-template.md).
2. **Re-run** the full import with **identical** files and options (simulated “accidental second run”).
3. Re-record counts.

## Pass criteria

- Counts for core objects **unchanged** (allow documented exceptions such as log-only rows).
- No duplicate **barcodes** or **internal references** where uniqueness is required.
- Spot-check **3** known external IDs still point to the same record (`id` stable).

## Fail criteria

- Any duplicate `res.partner` / `product.template` / `product.product` for same business identity.
- Stock quantities **doubled** without adjustment.

## On failure

- Fix tooling or mapping; update [external-id-convention.md](external-id-convention.md) or importer upsert mode.
- Re-test from clean snapshot.

## Record

| Test date | DB | First run count (products) | Second run count | Pass (Y/N) |
|-----------|-----|---------------------------|------------------|------------|
| | | | | |
