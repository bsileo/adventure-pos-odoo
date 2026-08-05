# Importing equipment

## Example file

Use the sample CSV:

`doc/import_examples/equipment_import_example.csv`

Import via **Equipment → Equipment → Favorites → Import records** (or list view import).

## Recommended columns

| Column | Tips |
|--------|------|
| `partner_id/name` | Must match an existing contact name (or use `partner_id/id` with external ID). |
| `category_id/id` | XML ID from data (e.g. `adventure_equipment.equipment_category_regulator`) or category name. |
| `product_id/name` | Optional; product must exist. Blank-fill runs on create. |
| `brand_name`, `model_name`, `manufacturer_sku` | Required for external gear without product; needed for serial uniqueness. |
| `serial_number` | Triggers primary identifier; respect [serial policy](SERIAL_POLICY.md). |
| `acquisition_source` | `shop_sale`, `other_shop`, `used`, `gift`, `migration`, etc. |
| `lifecycle_state` | Often `draft` or `active`; include `in_service_date` when activating. |
| `condition_state` | `new`, `excellent`, `good`, `fair`, `poor`, `damaged`, `unknown` |
| Warranty fields | `warranty_registered`, `warranty_lifetime`, `warranty_not_applicable`, dates |
| `origin_sale_ref` | Human-readable sale reference until sale/POS bridges exist |
| `ownership_verification_state` | `unverified`, `pending`, `verified`, `disputed` |

## Field tips

- **Equipment number** (`name`): leave empty or `New` to auto-assign from sequence.
- **Company**: defaults to your current company; set `company_id` for multi-company DBs.
- **Ownership history**: import sets `partner_id`; initial registration row is created on save.
- **Duplicates**: use `equipment_allow_duplicate_serial` only in custom import scripts if you must load conflicting legacy data.
- **Do not** import `warranty_status` — it is computed.

## After import

Review lifecycle state, activate if appropriate, and attach documents separately if needed.
