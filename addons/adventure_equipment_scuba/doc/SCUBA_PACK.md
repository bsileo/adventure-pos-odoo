# Scuba Equipment Pack

## Purpose

Layer scuba-specific service semantics on top of the generic
`adventure_equipment` + `adventure_equipment_service` stack without modifying
the sport-neutral engine.

## Service types

| Code | Name | Typical use |
|------|------|-------------|
| `SCUBA_VIP` | Cylinder VIP Inspection | Annual visual+ |
| `SCUBA_HYDRO` | Hydrostatic Test | 5-year requalification |
| `SCUBA_REG_SERVICE` | Regulator Service | Annual manufacturer service |
| `SCUBA_BCD_SERVICE` | BCD Service | Annual service |
| `SCUBA_O2_CLEAN` | Oxygen Clean Inspection | O₂ service / cleaning |
| `SCUBA_DRYSUIT_LEAK` | Drysuit Leak Test | Exposure suit leak check |
| `SCUBA_DC_SERVICE` | Dive Computer Service | Battery / manufacturer service |

## Default policies

Policies target existing equipment categories (`CYL`, `REG`, `BCD`, `DC`, `SUIT`).

| Policy | Interval | Category |
|--------|----------|----------|
| Cylinder VIP | 12 months | Cylinder |
| Cylinder Hydro | 5 years | Cylinder |
| Regulator Service | 12 months | Regulator |
| BCD Service | 12 months | BCD |
| Dive Computer Service | 24 months | Dive Computer |
| Drysuit Leak Test | 12 months | Exposure Suit |

Shops can override with brand/model policies (higher specificity) without code changes.

## Asset fields

Visible on the **Scuba** notebook page when the category is scuba-relevant.

Cylinder denormalized dates (`scuba_last_vip_date`, `scuba_last_hydro_date`) update when matching service records are completed, or via **Sync VIP/Hydro Dates**.

## Explicit non-goals

- Changing equipment lifecycle automatically when VIP/hydro is overdue
- Portal customer submission of VIP stickers
- Reminder emails (notifications module)
- Rental fleet tank fields (`adventure.rental.asset`) — sibling domain

## Extension

Further scuba rules (e.g. brand-specific regulator intervals) should be added as
additional `adventure.equipment.service.policy` records or thin inherits—not by
forking the generic service engine.
