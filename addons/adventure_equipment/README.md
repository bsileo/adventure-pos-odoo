# Adventure Equipment

Customer-owned equipment lifecycle registry for Adventure POS. This module records physical gear owned by contacts (regulators, computers, BCDs, cylinders, and similar durable items), separate from the shop **rental fleet** (`adventure_rental`).

## Purpose

- Register and track **customer-owned** equipment with optional catalog links, serial numbers, warranty metadata, and ownership history.
- Provide staff backend UI (list/form, partner smart button) and audit timeline events.
- Preserve **snapshots** when catalog products are archived or removed.

This module does **not** include service scheduling, customer portal, POS auto-registration, or kit/configuration management. Those live in planned `adventure_equipment_*` extension modules (see [Equipment management architecture](https://bsileo.github.io/adventure-pos-odoo/architecture/equipment-management/)).

## Install

1. Ensure dependencies are available: `adventure_base`, `contacts`, `product`, `mail`.
2. Install **Adventure Equipment** from Apps (or `-i adventure_equipment`). This module is an Odoo **application** (`application=True`), so it appears when filtering **Apps**. Supporting modules such as `adventure_equipment_service` use `application=False` and show under **Modules** / by category only.
3. Optional: load demo data when installing with demo enabled (`demo/demo_equipment.xml`).

After model or data changes, upgrade the module (`-u adventure_equipment`).

For the Tidewater Dive Shop demo, prefer installing **Adventure Equipment Scuba** (standard package via `seed-tidewater`), which pulls this registry in as a dependency.

## Ownership scope

- Current owner is stored on `partner_id` on each asset (**contact-only**).
- `res.partner.equipment_asset_count` counts assets where that exact partner is `partner_id`; it does **not** roll up child contacts or commercial partner hierarchies.
- Ownership transfers use the transfer wizard and append rows to ownership history.

## Portal and rental boundary

- **No customer portal** in this module; portal access is deferred to `adventure_equipment_portal`.
- **Not rental fleet** — do not use this module for shop-owned rentable assets; use `adventure_rental` instead.

## Import

Bulk load equipment via Odoo import on **Equipment** (`adventure.equipment.asset`). See `doc/import_examples/equipment_import_example.csv` for column names and sample rows.

Typical import fields: `partner_id`, `category_id`, `product_id` (optional), `brand_name`, `model_name`, `serial_number`, `acquisition_source`, `lifecycle_state`, warranty fields (`warranty_registered`, `warranty_lifetime`, `warranty_not_applicable`, dates), and `origin_sale_ref` for a human-readable sale reference.

Typed links to `sale.order` / POS lines and `stock.lot` are **not** implemented in Phase 1; use `origin_sale_ref` (Char) for provenance until bridge modules land.

## Security groups

| Group | Access |
|-------|--------|
| **Equipment Viewer** | Read-only |
| **Equipment User** | Create/edit (no unlink on assets) |
| **Equipment Manager** | Full access including unlink where policy allows |

## Tests

```bash
odoo -d <database> -u adventure_equipment --test-enable --stop-after-init \
  --test-tags /adventure_equipment
```

## Documentation

| Document | Description |
|----------|-------------|
| [STAFF_GUIDE.md](doc/STAFF_GUIDE.md) | Registering equipment (with/without product, serial, transfer, activate/retire/archive) |
| [DATA_MODEL.md](doc/DATA_MODEL.md) | Models and key fields |
| [LIFECYCLE.md](doc/LIFECYCLE.md) | Lifecycle states and transition table |
| [OWNERSHIP.md](doc/OWNERSHIP.md) | Contact-only scope, history, transfer wizard, verification |
| [PRODUCT_SNAPSHOTS.md](doc/PRODUCT_SNAPSHOTS.md) | Blank-fill vs refresh, ondelete set null |
| [SERIAL_POLICY.md](doc/SERIAL_POLICY.md) | Soft serial uniqueness and bypass context |
| [IMPORT.md](doc/IMPORT.md) | CSV import and field tips |
| [SECURITY.md](doc/SECURITY.md) | Groups, company rules, restricted fields |
| [LIMITATIONS.md](doc/LIMITATIONS.md) | Deferred features (portal, service, stock.lot, …) |
| [UPGRADE.md](doc/UPGRADE.md) | Module upgrade and versioning |

## Local smoke stack (optional)

This agent/CI helper uses the stock `odoo:19.0` image (no custom Dockerfile build):

```bash
docker compose -f docker-compose.smoke.yml up -d db
docker compose -f docker-compose.smoke.yml run --rm --no-deps odoo odoo \
  --db_host=127.0.0.1 --db_user=odoo --db_password=change_me_local_dev \
  -d smoke_equipment -i adventure_base,adventure_equipment --stop-after-init
docker compose -f docker-compose.smoke.yml run --rm --no-deps odoo odoo \
  --db_host=127.0.0.1 --db_user=odoo --db_password=change_me_local_dev \
  -d smoke_equipment -u adventure_equipment --test-enable --stop-after-init \
  --test-tags=/adventure_equipment
```

Requires host networking (as in `docker-compose.smoke.yml`) when Docker bridge networking is unavailable.
