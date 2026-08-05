# Upgrading adventure_equipment

## Command

After pulling code or changing models/data XML:

```bash
odoo -d <database> -u adventure_equipment --stop-after-init
```

Or **Apps → Adventure Equipment → Upgrade** in the UI.

Restarting Odoo alone does **not** apply schema or data changes.

## Versioning

Module version follows Odoo custom convention **`19.0.x.y.z`**:

- **19.0** — Odoo major series
- **x.y** — module milestone (1.0 = Phase 1 core registry)
- **z** — incremental dev/release counter (bump for each upgrade-worthy change)

Current release: **19.0.1.0.2**

## 19.0.1.0.2 notes

- Equipment number assignment uses `ir.sequence.with_company(company)` on create for multi-company safety.
- Sequence record remains shared (`company_id` False on `ir.sequence`); see [Limitations](LIMITATIONS.md).

## Tests after upgrade

```bash
odoo -d <database> -u adventure_equipment --test-enable --stop-after-init \
  --test-tags /adventure_equipment
```

## Dependencies

Requires: `adventure_base`, `contacts`, `product`, `mail`. Install or upgrade those first if needed.
