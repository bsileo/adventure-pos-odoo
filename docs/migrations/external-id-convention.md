# External ID convention for Dive Shop 360 migrations

**Goal:** Safe **re-import** and **idempotency** — running the same migration twice should not duplicate core business records when tooling honors these keys.

## Pattern

Use **`ir.model.data`** XML IDs (module-qualified) or Odoo **external id** column in CSV import:

```text
d360.{object}.{source_stable_id}
```

**Examples:**

- `d360.partner.12345`
- `d360.product.67890`
- `d360.product_tmpl.abc-dee` (if source UUID)

## Rules

1. **`source_stable_id`** must be stable in D360 exports across pulls. If only composite keys exist, hash a canonical string and document algorithm.
2. **Namespacing** — prefix `d360` avoids collision with master-catalog sync IDs (use a different prefix for master-originated data, e.g. `master.`).
3. **Per module** — CSV import often uses `id` column as external id; may prefix with `__import__.d360.partner.12345` depending on importer; follow chosen path in [odoo-import-tooling-evaluation.md](odoo-import-tooling-evaluation.md).
4. **Updates** — Second run with same external id should **update** same record when import mode supports it.

## Custom fields (optional)

For long-term traceability without relying only on `ir.model.data`, Adventure modules may add **`x_d360_id`** or `d360_external_ref` style fields — any schema change is **`risk:db-migration`** and needs a GitHub issue.

## Checklist

- [ ] Convention agreed for partners, products, variants (variant may need `d360.product` per `product.product` id)
- [ ] Documented in [dive-shop-360-odoo-mapping.md](dive-shop-360-odoo-mapping.md) idempotency column
- [ ] [idempotency-test-procedure.md](idempotency-test-procedure.md) verifies
