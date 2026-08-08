# Adventure Equipment Scuba

Dive-shop vertical pack for customer-owned scuba equipment.

## Depends

- `adventure_equipment_service` (and therefore `adventure_equipment`)

## App flag

This module is an Odoo **application** (`application=True`) so it appears when filtering **Apps** (not only under category *Adventure POS*). The generic service engine (`adventure_equipment_service`) stays `application=False` as a supporting module.

## What it adds

- Scuba **service types**: VIP, hydrostatic, regulator service, BCD service, oxygen clean, drysuit leak test, dive computer service
- Default **category-targeted policies** (VIP annual, hydro 5y, regulator/BCD annual, etc.)
- **Asset scuba fields** (cylinder pressures, gas compatibility, oxygen-clean, VIP/hydro denorm dates, regulator/BCD/suit metadata)
- **Service record scuba fields** (VIP sticker, hydro stamp, O₂ clean performed)
- Demo cylinder / regulator / BCD assets
- **Tidewater seed contributor** (`seeds/tidewater_seed.py`) — customer equipment for Maya Carter, Jon Ellis, Luis Romero, Nora Singh, and the Carter Family when `seed-tidewater` runs

## Tidewater standard package

Included in the Tidewater Dive Shop standard install set used by `make seed-tidewater` / sandbox bootstrap (alongside `dive_shop_pos`). No hard dependency on `dive_shop_pos`; the orchestrator skips this contributor when the module is not installed.

## Out of scope

- Portal, notifications, work orders, POS auto-create
- Scenario/readiness kits (`adventure_equipment_configuration`)
- Hard dependency on `dive_shop_pos`

See [docs](doc/SCUBA_PACK.md) and the [equipment management architecture](../../docs/architecture/equipment-management.md).
