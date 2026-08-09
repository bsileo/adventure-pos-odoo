# Adventure Equipment Configuration

Customer **packing lists** and **configurations** for `adventure.equipment.asset`.

## Models

- `adventure.equipment.configuration` — list header (`list_kind`: packing | configuration)
- `adventure.equipment.configuration.line` — members / checklist rows

## Behaviors

- `list_kind` cannot change after the first line exists
- Asset lines keep **snapshots**; asset archive/retire/unlink does **not** remove lines (broken-reference state)
- Quantity lines use `quantity` + Char `quantity_uom_label`

## Portal

Install `adventure_equipment_configuration_portal` for `/my/equipment/lists`.

## Design

See [Equipment lists & configurations (portal)](../../docs/architecture/equipment-lists-portal.md).
