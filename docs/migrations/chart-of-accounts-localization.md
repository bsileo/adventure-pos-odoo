# Chart of accounts and fiscal localization before migration loads

**Principle:** Company, **fiscal localization**, **chart of accounts**, journals, and tax templates must exist **before** importing transactional history or stock that posts to accounting.

Aligned with tenant baseline in [tenant provisioning](../architecture/tenant-provisioning.md) §4.2.

## Order of operations

1. Create or verify **`res.company`** — legal name, country, currency, timezone.
2. Install **fiscal localization** module(s) appropriate for the country (e.g. US localization).
3. Complete **chart of accounts** setup wizard or load standard CoA.
4. Configure **taxes** (sales tax) to match how the shop will operate in Odoo going forward — map D360 tax **labels** in [dive-shop-360-odoo-mapping.md](dive-shop-360-odoo-mapping.md) to Odoo tax records (may require one-time manual mapping table).
5. Verify **default accounts** on product categories / stock accounts for inventory valuation method in use.

## Migration-specific notes

- **Historical sales import** (if done) must use tax and journal configuration consistent with how entries are posted — coordinate with accountant.
- Opening balances may require **opening journal entries** separate from POS migration; document in validation report.

## Sign-off

| Check | Done (Y/N) | By / date |
|-------|------------|-----------|
| CoA live | | |
| Taxes configured | | |
| Stock valuation accounts | | |
| Accountant reviewed | | |
