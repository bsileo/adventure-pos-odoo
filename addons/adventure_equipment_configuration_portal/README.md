# Adventure Equipment Configuration Portal

Customer portal for packing lists and configurations.

## Routes

- `/my/equipment/lists` — index (filter packing / configuration)
- `/my/equipment/lists/new` — create
- `/my/equipment/lists/<id>` — checklist detail (free-text add + equipment autocomplete)
- `/my/equipment/lists/<id>/suggest` — JSON autocomplete for owned equipment
- `/my/equipment/lists/<id>/edit` — header edit

## Checklist UX

Type an item and press **Add** to save a plain checklist row. Matching owned equipment appears as you type (loose search across nickname, category, brand/model, manufacturer, serial, notes, tags, and product snapshots); choosing a suggestion links that asset. Converting a plain item into registered equipment is deferred.

## List index health

There is no Status column. When linked equipment is archived, unavailable, or missing, a warning icon appears at the left of that row; hover or tap/focus explains that the list may be invalid until updated.

## Install

Depends on `adventure_equipment_configuration` and `adventure_equipment_portal`.

## Design

[Equipment lists & configurations (portal)](../../docs/architecture/equipment-lists-portal.md)
