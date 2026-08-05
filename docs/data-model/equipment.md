# Equipment registry (Phase 1)

**Module:** `adventure_equipment` — customer-owned gear lifecycle registry (not rental fleet).

## Scope

Records physical items owned by contacts: regulators, computers, BCDs, cylinders, etc. Optional link to `product.product`; serial numbers; warranty metadata; ownership history; documents; audit events.

**Not in Phase 1:** portal, service orders, `stock.lot`, typed sale/POS auto-registration, kit configurations. See [Equipment management](../architecture/equipment-management.md) for the full roadmap.

## Core models

| Model | Role |
|-------|------|
| `adventure.equipment.asset` | Main equipment record |
| `adventure.equipment.category` | Equipment taxonomy (hierarchical) |
| `adventure.equipment.tag` | Labels |
| `adventure.equipment.identifier` | Typed identifiers (serial, RFID, …) |
| `adventure.equipment.ownership` | Ownership history rows |
| `adventure.equipment.document` | Attachments and document metadata |
| `adventure.equipment.event` | Read-only timeline |

Partner extension: `res.partner.equipment_asset_count` (contact-only, no parent rollup).

## Key behaviors

- **Lifecycle** — states from `draft` through `active`, service/loan/lost paths, to `retired` / `disposed`; separate from archive (`active` flag).
- **Ownership** — `partner_id` + transfer wizard; verification states `unverified` → `verified` / `disputed`.
- **Catalog** — optional product link; snapshot fields survive product archive/unlink (`ondelete set null`).
- **Serial** — soft-unique per company + brand + model (case-insensitive).
- **Security** — Viewer / User / Manager groups; `purchase_price` manager-only; multi-company rules.

## Deeper reference

- Architecture: [Equipment management](../architecture/equipment-management.md)
- Module README and staff docs: `addons/adventure_equipment/README.md` and `addons/adventure_equipment/doc/`
