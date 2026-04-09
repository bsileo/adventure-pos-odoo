# Catalog strategy for shops migrating from Dive Shop 360

**Decision affects:** Product import path, master catalog involvement, ongoing updates.

Adventure POS assumes a **master catalog** environment for governed catalog data and **tenant operational databases** per shop. See [core-model.md](../data-model/core-model.md).

## Options

### A — Tenant-local catalog from D360

- Import D360 products into the **tenant DB** as **`tenant_local`** (or equivalent `product_origin`) with no master linkage initially.
- **Pros:** Fastest cutover; matches shop’s current assortment exactly.
- **Cons:** Duplicated catalog semantics across tenants; later alignment to master requires matching or migration.

### B — Baseline from master catalog release only

- Tenant receives products primarily from an **approved catalog release**; D360 export used only for **stock levels, pricing, and gaps**.
- **Pros:** Clean canonical data; best for shops that already match master assortment.
- **Cons:** Heavy upfront mapping from D360 → canonical SKUs; may miss odd local-only items without a gap process.

### C — Hybrid (recommended default to evaluate)

- Apply **master baseline** for products that **match** on trusted key (e.g. GTIN/UPC, vendor SKU rule).
- Create **tenant_local** rows for **non-matching** D360 lines.
- Maintain **`master_catalog_id` / external refs** where matched for future sync.

## Recorded decision (fill in)

| Field | Value |
|-------|--------|
| Chosen strategy | A / B / C |
| Matching keys (if hybrid) | e.g. barcode, internal SKU |
| Fallback for no match | tenant_local product |
| Who approves exceptions | |

## Implementation notes

- If **C**, document the **staged order**: master sync (or release apply) **before** or **after** D360 product import — avoid double SKUs with conflicting barcodes.
- Cross-reference [stock-opening-valuation-strategy.md](stock-opening-valuation-strategy.md) so opening stock lands on the correct `product.product` rows.
