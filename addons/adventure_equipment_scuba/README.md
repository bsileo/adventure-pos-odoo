# Adventure Equipment Scuba

Dive-shop vertical pack for customer-owned scuba equipment.

## Depends

- `adventure_equipment_service` (and therefore `adventure_equipment`)

## What it adds

- Scuba **service types**: VIP, hydrostatic, regulator service, BCD service, oxygen clean, drysuit leak test, dive computer service
- Default **category-targeted policies** (VIP annual, hydro 5y, regulator/BCD annual, etc.)
- **Asset scuba fields** (cylinder pressures, gas compatibility, oxygen-clean, VIP/hydro denorm dates, regulator/BCD/suit metadata)
- **Service record scuba fields** (VIP sticker, hydro stamp, O₂ clean performed)
- Demo cylinder / regulator / BCD assets

## Out of scope

- Portal, notifications, work orders, POS auto-create
- Scenario/readiness kits (`adventure_equipment_configuration`)
- Hard dependency on `dive_shop_pos`

See [docs](doc/SCUBA_PACK.md) and the [equipment management architecture](../../docs/architecture/equipment-management.md).
