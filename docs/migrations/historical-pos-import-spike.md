# Historical POS / sales import spike (recent window)

**Label for issues:** `risk:db-migration`  
**Scope:** Import **12–24 months** (configurable) of sales-like history for reporting or customer lookups without breaking stock or accounting.

## Why this is risky

- **`pos.order`** history creates payments, stock moves, and accounting entries depending on configuration and import method.
- Double-counting with [stock-opening-valuation-strategy.md](stock-opening-valuation-strategy.md) if both historical moves and opening quants apply to the same physical goods.
- Tax periods may be **closed**; back-posting can disturb books — **accountant must approve**.

## Options to evaluate

| Approach | Description | Stock impact | Accounting |
|----------|-------------|--------------|------------|
| **Full POS documents** | Create historical `pos.order` in closed state | High — must reconcile with opening | Posts history periods |
| **Sale orders only** | `sale.order` archived / done | Similar concerns | Similar |
| **Non-posting order archive** | Import historical invoice/order headers and lines into archive models linked to customers/products when matched | None | None |
| **Journal-only memorial** | Aggregate per day into GL memo (non-item level) | Low | Accountant-driven |
| **No financial posting** | Attach summarized report; partner **sales stat** fields if available | None | None — may be insufficient |
| **Separate “archive” DB** | Keep D360 export query offline | None in live Odoo | None |

## D360 transaction summary report evaluation

Sample reviewed: `sample_data/Report_builder_1777175252.xlsx`.

This report is line-level transaction history, not just invoice totals. It is a strong candidate for building **customer sales/order history** in Adventure POS as a **non-posting archive**, but it should not be treated as safe input for live `pos.order` / `sale.order` reconstruction without additional source data and finance sign-off.

Observed sample shape:

| Metric | Observation |
|--------|-------------|
| Rows | 1,359 transaction lines |
| Unique invoices | 366 |
| Unique customers | 227 |
| Date range | `2026-01-02 12:40:40` through `2026-04-25 14:35:05` |
| Product identifiers | `Part number` and `Barcode` present on nearly all rows |
| Customer identifiers | `Customer ID` present on nearly all rows, with repeated customer contact snapshot fields |
| Invoice grouping | In the sample, invoice numbers did not map to multiple customers or multiple dates |
| Returns/adjustments | Negative `Sold Qty` rows and nonzero `Returned Qty` rows exist |
| Duplicate-looking rows | Exact duplicate-looking rows exist and need interpretation before import |

Available field groups include:

- customer snapshot: `Customer ID`, first/last name, email, address, phone, customer type
- order header: location, invoice type, invoice number, date, sales person
- product line: part number, barcode, description, serial number, category, vendor, department, manufacturer, taxable
- amounts: sold quantity, unit price, extended price, taxes, delivered/returned quantities, cost, extended cost, margin
- service/context: technician, instructor, color and size fields

## Recommended approach: non-posting order archive

Use this report to build an **order history by customer** for service lookup and reporting, not operational financial/stock history.

Recommended import target:

- `adventure.history.order` (or similarly named archive header model)
- `adventure.history.order.line` (archive line model)

Recommended behavior:

1. Group rows into an archive order header by `Location + Invoice number` (include `Date` as a validation field).
2. Create archive lines for each source row.
3. Link to `res.partner` when customer matching is confident.
4. Link to `product.product` when product matching is confident.
5. Preserve the original source customer/product snapshots on the archive records even when matches succeed.
6. Keep unmatched customer/product lines importable and reviewable rather than forcing weak matches.
7. Do **not** create payments, stock moves, accounting entries, or active `pos.order` / `sale.order` records during the first implementation.

This gives AdventOps:

- customer purchase history
- product/service line history
- category/vendor/manufacturer sales history
- repair/service item lookup by customer
- sales summaries by customer and product family

without disturbing live inventory or accounting.

## Customer matching strategy

Match report rows to customers in this order:

1. D360 `Customer ID` to an external ID or dedicated source key, e.g. `d360.partner.{Customer ID}`.
2. Normalized exact email match.
3. Normalized phone match.
4. Name + address fallback.
5. If no confident match exists, keep the customer snapshot on the archive order and mark it unmatched.

Import should deduplicate customers before linking history because each line repeats the same customer fields.

## Product matching strategy

Match report lines to products in this order:

1. `Barcode` exact match against `product.product.barcode` or source reference records.
2. `Part number` exact match against local SKU / `default_code` or a dedicated D360 product reference.
3. Composite match using part number + vendor/manufacturer + description.
4. Assisted/fuzzy review using description, category, department, manufacturer, color, and size.
5. If no confident match exists, keep the product snapshot on the archive line and mark it unmatched.

The report's `Category`, `Vendor`, `Department`, and `Manufacturer` are useful matching and reporting hints, but they should not be treated as authoritative master catalog governance data without review.

## Idempotency and duplicate handling

The sample report does not expose an obvious stable line ID. Header idempotency can likely use:

`d360.history_order.{Location}.{Invoice number}`

Line idempotency needs a deterministic strategy. Candidate:

`d360.history_order_line.{Location}.{Invoice number}.{line_sequence}`

Where `line_sequence` is assigned after stable sorting within an invoice by source row order.

Before implementation, confirm how to handle duplicate-looking rows:

- repeated service lines may represent real repeated units and should be preserved
- exact duplicate export rows may need collapse or review
- negative quantity rows and `Returned Qty` rows should be imported as return/adjustment lines, not silently dropped

## Open questions before implementation

1. Can D360 export a line-level unique ID, invoice total, payment/tender summary, discount fields, and tax total?
2. Is `Invoice number` globally unique across all locations, or only unique within `Location`?
3. Are exact duplicate-looking service rows legitimate repeated work/items?
4. How should returns, exchanges, and voids be represented in the archive UI?
5. Should unmatched archive products be available for later rematching to the product catalog?
6. How much history should be backfilled initially: 12 months, 24 months, or all available?

## Spike deliverables (engineering + finance)

1. Decision record: chosen approach + **signed by accountant**.
2. Prototype on **copy DB**: N-month subset; measure import runtime, match rates, and archive usability.
3. Rollback: restore DB snapshot if prototype wrong.
4. Update [dive-shop-360-odoo-mapping.md](dive-shop-360-odoo-mapping.md) historical rows.

## Outcome template

| Question | Answer |
|----------|--------|
| Final approach | Recommended: non-posting historical order archive |
| Affects stock? | No |
| Fiscal periods touched? | No, unless future phase creates accounting documents |
| Pilot issue | |
