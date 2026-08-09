# Equipment registry and service

**Modules:**

- `adventure_equipment` — customer-owned gear lifecycle registry (not rental fleet)
- `adventure_equipment_service` — generic service types, policies, requirements, records
- `adventure_equipment_scuba` — scuba service types/policies and scuba asset/record fields

## Registry scope (Phase 1)

Records physical items owned by contacts: regulators, computers, BCDs, cylinders, etc. Optional link to `product.product`; serial numbers; warranty metadata; ownership history; documents; audit events.

## Service scope (Phase 3A / architecture Phase 2)

Sport-neutral maintenance forecasting and history.

## Scuba scope (Phase 3B)

VIP, hydrostatic, regulator/BCD/computer/drysuit service types and default category policies; cylinder gas/pressure/oxygen-clean fields; VIP/hydro denormalized dates. See `addons/adventure_equipment_scuba/doc/SCUBA_PACK.md`.

**Still deferred:** notifications, work orders, `stock.lot`, typed sale/POS auto-registration, kit/packing lists (portal design: [Equipment lists & configurations](../architecture/equipment-lists-portal.md)). Portal registry MVP is in progress — see [Client web portal](../architecture/client-web-portal.md). Core reference: [Equipment management](../architecture/equipment-management.md).

## Core models

| Model | Role |
|-------|------|
| `adventure.equipment.asset` | Main equipment record (+ service rollup fields from service module) |
| `adventure.equipment.category` | Equipment taxonomy (hierarchical) |
| `adventure.equipment.tag` | Labels |
| `adventure.equipment.identifier` | Typed identifiers (serial, RFID, …) |
| `adventure.equipment.ownership` | Ownership history rows |
| `adventure.equipment.document` | Attachments and document metadata |
| `adventure.equipment.event` | Read-only timeline |
| `adventure.equipment.service.type` | Configurable service / inspection kinds |
| `adventure.equipment.service.policy` | Targeting + schedule rules |
| `adventure.equipment.service.requirement` | Per-asset maintenance obligations |
| `adventure.equipment.service.record` | Completed / verified / voided history |

Partner extensions:

- `equipment_asset_count` (contact-only)
- `equipment_service_due_soon_count` / `due` / `overdue` + `equipment_next_service_due_date` (contact-only)

## Key behaviors

- **Lifecycle** — operational state on the asset; separate from maintenance status.
- **Service status** — computed/aged on requirements; rolled up to the asset; does not auto-set `out_for_service`.
- **Policy matching** — structured fields only; one winning policy per service type; manual requirements coexist.
- **Date aging** — stored dates + recomputed status on write/cron (calendar months/years).
- **History** — completed/verified service records are protected; void + replace for corrections.
- **Security** — reuses Equipment Viewer / User / Manager; multi-company rules on all service models.

## Deeper reference

- Architecture: [Equipment management](../architecture/equipment-management.md)
- Service engine: `addons/adventure_equipment_service/doc/SERVICE_ENGINE.md`
- Registry module: `addons/adventure_equipment/README.md`
