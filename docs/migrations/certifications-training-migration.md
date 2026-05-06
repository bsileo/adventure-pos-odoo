# Certifications and training data (Dive Shop 360 → Adventure)

Dive Shop 360 may export **certification** and related **training** records (verify in [dive-shop-360-export-inventory.md](dive-shop-360-export-inventory.md)).

Adventure POS **v1** focuses on retail POS, inventory, and customers (see [agent-rules.md](../agent-rules.md)). Native Odoo may not model every dive-agency field without customization.

**Related (future greenfield design, not migration scope):** a planned **scuba training and scheduling** architecture for operational classes—not the same topic as importing D360 historical rows—is documented in [Scuba training and scheduling (future)](../architecture/scuba-training-scheduling.md). Treat that page as **design-only** until prioritized.

## Decision options

### Option 1 — Archive-only (lowest engineering)

- Store **PDF/CSV exports** in document management or secure storage; link from `res.partner` as attachments or notes when useful.
- **Pros:** No schema work; satisfies “we have a copy.”
- **Cons:** Not queryable inside Odoo for renewal workflows.

### Option 2 — Lightweight partner notes

- Summarize certification status in **partner chatter / internal notes** during migration.
- **Pros:** Staff-visible without new models.
- **Cons:** Unstructured; hard to report on.

### Option 3 — Custom model (future `adventure_customers` or similar)

- Add a small model, e.g. `x_certification_line` or `adventure.certification.record`, linked to `res.partner`, keyed by D360 id for idempotency.
- **Pros:** Structured queries, room for expiry alerts later.
- **Cons:** Requires module design, access rules, migration tooling; tag **`risk:db-migration`**.

## Recorded decision

| Field | Value |
|-------|--------|
| Chosen option | 1 / 2 / 3 |
| Fields to capture (if 3) | agency, level, number, dates, instructor, … |
| Pilot issue link | |

If Option 3 is chosen, add rows to [dive-shop-360-odoo-mapping.md](dive-shop-360-odoo-mapping.md) and track work in GitHub with **`module:adventure_customers`** (or agreed module) when that module exists.
