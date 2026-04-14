# Cutover weekend checklist — Dive Shop 360 → Adventure POS

Use with [runbook-phases-and-checkpoints.md](runbook-phases-and-checkpoints.md). Adjust times for your timezone and shop hours.

## Pre-cutover (T-48h to T-0)

- [ ] All staging dry-runs complete; [validation-report-template.md](validation-report-template.md) archived
- [ ] Mapping frozen per change-control (except agreed hotfixes)
- [ ] Tenant DB provisioned; modules installed per [tenant provisioning](../architecture/tenant-provisioning.md)
- [ ] Chart of accounts and fiscal localization applied — [chart-of-accounts-localization.md](chart-of-accounts-localization.md)
- [ ] POS config shell: session, journal, default payment methods placeholders
- [ ] Staff [training-hypercare-checklist.md](training-hypercare-checklist.md) dry practice scheduled

## Freeze (T-0)

- [ ] **Announce freeze** — no new sales, returns, or inventory adjustments in D360 (or agreed minimal exceptions documented)
- [ ] Final **D360 exports** pulled; record **UTC timestamp** and operator
- [ ] Backup **Odoo database** before bulk import (if not empty)

## Import order (do not skip without reason)

Order avoids foreign-key and stock double-counting issues. Align with [stock-opening-valuation-strategy.md](stock-opening-valuation-strategy.md).

1. [ ] Reference data: **uom**, **categories**, **payment methods** (if importing), **pricelist** shells
2. [ ] **Products** (templates/variants per catalog strategy)
3. [ ] **Stock**: opening quants or scripted adjustments on **cutover date**
4. [ ] **Partners** (customers / suppliers as needed)
5. [ ] **Open documents** (if any): draft SO/PO only if explicitly in scope
6. [ ] **Historical window** (optional): recent POS/sales per [historical-pos-import-spike.md](historical-pos-import-spike.md)

## Post-import smoke tests (before opening doors)

- [ ] Log into POS; start session
- [ ] Sell one **in-stock** item; **payment** completes; receipt prints or emails
- [ ] **Return** or refund flow (if used)
- [ ] **Stock adjustment** or internal transfer (if multi-location)
- [ ] Spot-check **3** migrated customers in POS lookup
- [ ] Run validation tallies from [validation-report-template.md](validation-report-template.md)

## Go-live

- [ ] Accountant sign-off on opening stock / bridge entries
- [ ] **Hypercare** window started; escalation contacts distributed

## Artifacts to retain

- Export file checksums or hashes
- Import logs
- Completed validation report
