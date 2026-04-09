# Migrations

Documentation for moving customers from external systems into Adventure POS (Odoo 18).

## Dive Shop 360

| Document | Purpose |
|----------|---------|
| [dive-shop-360-export-inventory.md](dive-shop-360-export-inventory.md) | Per-object export surface (paths, formats) — **fill during discovery** |
| [sample-exports-pii-and-retention.md](sample-exports-pii-and-retention.md) | Sample data handling, parallel-run and retention policy |
| [dive-shop-360-odoo-mapping.md](dive-shop-360-odoo-mapping.md) | D360 → Odoo mapping matrix template |
| [catalog-strategy-migrated-shops.md](catalog-strategy-migrated-shops.md) | Master catalog vs tenant-local vs hybrid |
| [certifications-training-migration.md](certifications-training-migration.md) | Certification / training records decision |
| [runbook-phases-and-checkpoints.md](runbook-phases-and-checkpoints.md) | Migration phases and rollback triggers |
| [runbook-cutover-weekend.md](runbook-cutover-weekend.md) | Cutover weekend checklist |
| [validation-report-template.md](validation-report-template.md) | Post-import validation structure |
| [odoo-import-tooling-evaluation.md](odoo-import-tooling-evaluation.md) | UI import, RPC, shell — tooling choice |
| [chart-of-accounts-localization.md](chart-of-accounts-localization.md) | CoA and fiscal baseline before transactional loads |
| [stock-opening-valuation-strategy.md](stock-opening-valuation-strategy.md) | Opening stock vs recent history window |
| [d360-csv-normalizer-spec.md](d360-csv-normalizer-spec.md) | Optional normalizer pre-Odoo |
| [external-id-convention.md](external-id-convention.md) | `d360.*` external IDs and idempotency |
| [historical-pos-import-spike.md](historical-pos-import-spike.md) | Recent-window history import — fiscal and technical risks |
| [pilot-dry-run-procedure.md](pilot-dry-run-procedure.md) | Staging dry-run steps |
| [idempotency-test-procedure.md](idempotency-test-procedure.md) | Double-import verification |
| [training-hypercare-checklist.md](training-hypercare-checklist.md) | Staff training and go-live support |

## Related architecture

- [Core data model](../data-model/core-model.md)
- [Product catalog model](../data-model/product-catalog.md)
- [Tenant provisioning](../architecture/tenant-provisioning.md)
- [Development tracking (issues / labels)](../development-tracking.md) — use `risk:db-migration` for schema-heavy migration work
