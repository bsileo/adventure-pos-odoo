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
| **Journal-only memorial** | Aggregate per day into GL memo (non-item level) | Low | Accountant-driven |
| **No financial posting** | Attach summarized report; partner **sales stat** fields if available | None | None — may be insufficient |
| **Separate “archive” DB** | Keep D360 export query offline | None in live Odoo | None |

## Spike deliverables (engineering + finance)

1. Decision record: chosen approach + **signed by accountant**.
2. Prototype on **copy DB**: N-month subset; measure runtime and posted entries.
3. Rollback: restore DB snapshot if prototype wrong.
4. Update [dive-shop-360-odoo-mapping.md](dive-shop-360-odoo-mapping.md) historical rows.

## Outcome template

| Question | Answer |
|----------|--------|
| Final approach | |
| Affects stock? | |
| Fiscal periods touched? | |
| Pilot issue | |
