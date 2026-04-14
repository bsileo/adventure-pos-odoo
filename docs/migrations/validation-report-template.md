# Migration validation report template

**Customer / tenant:** _________________________  
**Date:** _________________________  
**Exported from D360 (timestamp):** _________________________  
**Imported into Odoo (timestamp):** _________________________  
**Odoo DB name / environment:** _________________________

## 1. Row counts

| Object | Source rows | Imported / created | Failed / skipped | Notes |
|--------|-------------|--------------------|------------------|-------|
| Products | | | | |
| Variants | | | | |
| Customers | | | | |
| Stock lines / quants | | | | |
| Historical orders (if in scope) | | | | |

## 2. Hash or aggregate checks (optional)

| Check | Source value | Odoo value | Match (Y/N) |
|-------|--------------|------------|-------------|
| Sum of qty × cost (sanity) | | | |
| Count active products | | | |
| Count partners with email | | | |

## 3. Spot checks

| SKU or partner | Expected | Observed | OK (Y/N) |
|----------------|----------|----------|----------|
| | | | |
| | | | |
| | | | |

## 4. Open items

| Item | Severity | Owner |
|------|----------|-------|
| | | |

## 5. Accounting handoff

- Opening inventory journal: reference _________________
- GL bridge / cutover memo: _________________
- Accountant sign-off: _________________ Date: _______

## 6. Sign-off

| Role | Name | Signature / date |
|------|------|------------------|
| Shop | | |
| Implementation | | |
