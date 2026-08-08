# Security

## Groups

| Group | Technical ID | Access |
|-------|----------------|--------|
| **Equipment Viewer** | `adventure_equipment.group_equipment_viewer` | Read-only on equipment models |
| **Equipment User** | `adventure_equipment.group_equipment_user` | Create and edit; **no unlink** on assets |
| **Equipment Manager** | `adventure_equipment.group_equipment_manager` | Full CRUD where business rules allow |

Viewer implies internal user (`base.group_user`). User implies Viewer. Manager implies User.

## Company rules

Record rules on asset, ownership, document, event, identifier, category, and tag:

```text
['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
```

Users see records for their allowed companies (or shared records with no company).

## Restricted fields

| Field | Restriction |
|-------|-------------|
| `purchase_price` | **Equipment Manager** only (`groups` on field) |
| `internal_note` | **Equipment User** and above (not Viewer) |

`customer_note` is visible to all groups that can read the asset (portal display deferred).

## Asset deletion

Even **Manager** cannot unlink assets that fail business rules (non-draft lifecycle, documents, extended history) — see [Lifecycle](LIFECYCLE.md).

## Events

`adventure.equipment.event` is read-only for normal users; writes require context `equipment_allow_event_write`.

## Wizard

Ownership transfer wizard: User (create/write), Manager (full).
