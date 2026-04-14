# Pilot dry-run procedure (staging)

**Prerequisites:** [runbook-phases-and-checkpoints.md](runbook-phases-and-checkpoints.md) discovery phase complete; staging tenant DB available.

## Steps

1. **Provision** staging database matching production module set ([tenant provisioning](../architecture/tenant-provisioning.md)).
2. **Load fiscal baseline** per [chart-of-accounts-localization.md](chart-of-accounts-localization.md).
3. **Run import pipeline** in agreed order ([runbook-cutover-weekend.md](runbook-cutover-weekend.md) import order section).
4. **Capture metrics:**
   - Wall-clock time per step
   - Peak memory (if scripted)
   - Error count / retries
5. **Complete** [validation-report-template.md](validation-report-template.md).
6. **Execute** [idempotency-test-procedure.md](idempotency-test-procedure.md) on a **disposable DB copy** if destructive.
7. **Debrief** — log gaps in [dive-shop-360-odoo-mapping.md](dive-shop-360-odoo-mapping.md) gap table.

## Exit criteria for pilot → production

- Validation within agreed tolerances ([runbook-phases-and-checkpoints.md](runbook-phases-and-checkpoints.md) rollback section).
- Shop owner + accountant acknowledgment.
- POS smoke tests passed on staging.

## Record

| Pilot date | Shop (code name) | DB snapshot id | Outcome |
|------------|------------------|----------------|---------|
| | | | |
