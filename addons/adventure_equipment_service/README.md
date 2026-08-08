# Adventure Equipment Service

Generic, sport-neutral service lifecycle engine for customer-owned equipment.

## Depends

- `adventure_equipment`
- `mail`

## Models

| Model | Purpose |
|-------|---------|
| `adventure.equipment.service.type` | Configurable service / inspection kinds |
| `adventure.equipment.service.policy` | Reusable targeting + schedule rules |
| `adventure.equipment.service.requirement` | Per-asset maintenance obligations |
| `adventure.equipment.service.record` | Completed / verified / voided history |

## Out of scope (Phase 3A)

- Scuba-specific VIP/hydro/regulator rules (`adventure_equipment_scuba`)
- Portal, notifications, work orders, POS/sale bridges

See [Equipment management architecture](../../docs/architecture/equipment-management.md)
and [module docs](doc/).
