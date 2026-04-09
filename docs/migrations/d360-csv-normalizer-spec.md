# D360 CSV normalizer (optional tool) — specification

**Purpose:** When Dive Shop 360 exports are inconsistent or not Odoo-ready, a small **preprocessor** normalizes files before UI import or RPC load.

**Implementation options:** Standalone Python in `scripts/migrations/` (future) or Odoo transient wizard module. This document is the **spec**; code is optional until pilot proves need.

## Inputs

- One or more CSV/XLSX files per object type (products, customers, …).
- **Config:** column rename map, encoding (UTF-8 vs Windows-1252), delimiter, date format.

## Behaviors

| Behavior | Description |
|----------|-------------|
| Charset fix | Normalize to UTF-8; strip BOM |
| Column mapping | Source header → Odoo import header |
| Split / merge | e.g. “Full name” → `name`; “City, ST ZIP” parsed if needed |
| Dedupe | Keyed by [external-id-convention.md](external-id-convention.md) source id |
| Validation | Row-level errors written to `errors.csv` with line numbers |
| PII logging | No customer PII in logs; redact in error samples |

## Outputs

- `*_odoo_ready.csv` per entity, or JSON payloads for RPC.
- Summary: row count in/out, drop count, duplicate count.

## PII handling

- Document where intermediate files live; encrypt at rest; retention per [sample-exports-pii-and-retention.md](sample-exports-pii-and-retention.md).
- **Never** commit raw outputs with PII.

## When to build

- [ ] Pilot shows >X% rows fail on naive import due to formatting
- [ ] Multiple customers need same transforms (reuse pays off)

## Future code location

If implemented: `scripts/migrations/README.md` should point here; keep scripts **off** production credentials in repo.
