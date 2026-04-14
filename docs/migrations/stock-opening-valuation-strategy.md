# Stock opening and valuation strategy (D360 → Odoo)

**Context:** Backlog assumes **recent-window** sales history (e.g. 12–24 months) **plus** correct **opening stock** on go-live. Bad ordering **double-counts** inventory (history consumes stock and opening quants also claim stock).

## Goals

- On cutover date, **on-hand in Odoo** matches physical/D360 **after** agreed freeze.
- **Costing / valuation** matches shop and accountant expectations (standard vs FIFO, etc.—Odoo defaults per configuration).

## Recommended approach (conceptual)

1. **Import products** first (no stock yet, or stock ignored if import includes zero).
2. Choose **one** of:
   - **A — Opening inventory workflow** — Use Odoo’s intended flow for initial stock (inventory adjustment with default stock account), dated on **cutover date**.
   - **B — Scripted quants** — Only if team has proven patterns; requires Odoo expertise; tag **`risk:db-migration`**.
3. **Historical sales** (if imported): ensure transaction dates are **before** opening stock date **or** historical import does **not** create stock moves that conflict with opening — usually historical import is **posted in past** and opening is **as of cutover**, so **clear the rule**:

**Rule of thumb:** Opening stock reflects **as-of cutover** after freeze. Historical window in Odoo is for **reporting / customer history**; stock moves from that history should **not** leave negative or duplicate on-hand on go-live. If full `pos.order` history is loaded with stock moves, **do not** also load full current D360 qty without **negating** history effect — prefer accountant-reviewed approach from [historical-pos-import-spike.md](historical-pos-import-spike.md).

## Multi-location

- If D360 exports qty **per location**, map to Odoo **stock locations** before summing.
- Serialized items: confirm Odoo tracking (lot/serial) vs aggregate qty.

## Validation

- Reconcile total **valuation** from Odoo vs D360 export (rough sanity).
- Include stock section in [validation-report-template.md](validation-report-template.md).

## Recorded decision

| Field | Value |
|-------|--------|
| Opening stock method | A / B |
| Cutover date (inventory) | |
| Historical import affects stock? | Y / N (must align with accountant) |
