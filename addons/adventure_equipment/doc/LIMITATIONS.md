# Limitations (Phase 1)

The core `adventure_equipment` module is a **registry**. The following are **deferred** to extension modules or later phases:

| Area | Status |
|------|--------|
| Customer portal | `adventure_equipment_portal` — view own gear, upload documents |
| Service scheduling / work orders | `adventure_equipment_service` |
| `stock.lot` linkage | Serial sync with inventory lots |
| Typed **sale.order** / **POS** registration | Use `origin_sale_ref` (Char) for now |
| Kit / configuration management | Bundled gear, component trees |
| Notifications | Warranty expiry, service due reminders |

## Implemented in core

- Manual and import registration
- Optional product link with snapshots
- Ownership history and transfer wizard
- Lifecycle states and audit events
- Documents (attachments)
- Warranty metadata (computed status)
- Multi-company record rules

## Sequence note

Equipment numbers use shared sequence `adventure.equipment.asset` (`company_id` = False on `ir.sequence`). `create()` calls `next_by_code` with `with_company(company)` so multi-company environments get consistent numbering behavior. Per-company sequence splits are not implemented in Phase 1.

## Rental boundary

Shop **rental fleet** belongs in `adventure_rental`, not this module.
