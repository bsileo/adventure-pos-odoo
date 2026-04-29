# Dive Shop 360 → Odoo 19 / Adventure — mapping matrix

**Status:** Template — one row per source object or report column group.

**Related:** [product-catalog.md](../data-model/product-catalog.md) (product origin, master sync fields), [core-model.md](../data-model/core-model.md).

## Column guide

| Column | Meaning |
|--------|---------|
| **Source entity** | D360 object or export name |
| **Source field** | Column or API field |
| **Odoo model** | Technical model name (e.g. `product.template`) |
| **Odoo field** | Destination field |
| **Transform** | Units, rounding, split/join, default if empty |
| **Required** | Y/N for go-live minimum |
| **Owner** | `master` (master catalog env), `tenant` (shop DB), or `either` |
| **Idempotency key** | Stable source id for [external-id-convention.md](external-id-convention.md) |

## Matrix (fill during discovery)

| Source entity | Source field | Odoo model | Odoo field | Transform | Required | Owner | Idempotency key |
|---------------|--------------|------------|------------|-----------|----------|-------|-----------------|
| Customer | *TBD* | `res.partner` | `name`, `email`, … | | Y | tenant | `d360.partner.{id}` |
| Product | *TBD* | `product.template` / `product.product` | | | Y | tenant or master * | `d360.product.{id}` |
| Category | *TBD* | `product.category` | | | N | tenant | |
| Stock qty | *TBD* | stock quant / adjustment workflow | | | Y | tenant | |
| POS line history | *TBD* | `pos.order` / alt. journaling | | See [historical-pos-import-spike.md](historical-pos-import-spike.md) | N | tenant | |

\* Product owner depends on [catalog-strategy-migrated-shops.md](catalog-strategy-migrated-shops.md).

## Gap log

| Gap | Impact | Resolution (issue / doc) |
|-----|--------|---------------------------|
| Example: D360 bundles not representable as Odoo BOM | Medium | Document manual fix or future module |
| | | |

## Sign-off

- Mapping reviewed by: _________________ Date: _______
- Pilot dry-run completed: _________________
