# Ownership

## Contact-only scope

- **Current owner** is `partner_id` on `adventure.equipment.asset`.
- `res.partner.equipment_asset_count` counts assets where that exact partner is `partner_id`.
- **No rollup** to parent companies or commercial partners — a BCD registered on a club member does not increment the club’s count.

Register organization-owned gear on the **company** partner with `ownership_type` = **Organization**. Register individual gear on the **person** contact.

## Ownership types

| Value | Use |
|-------|-----|
| `customer` | Default; individual owner |
| `organization` | Club, team, or business partner |
| `shop` | Shop-held customer gear (limited Phase 1 use) |

## History model

`adventure.equipment.ownership` stores an append-only timeline:

- One row with `is_current` = True per asset (enforced by constraint).
- Previous rows get `date_to` set when a transfer closes them.
- `change_type`: registration, sale, transfer, correction, migration.

On **create**, an initial registration row is opened. On **partner change** (form or wizard), `_transfer_ownership` closes the current row and opens a new one.

## Transfer wizard

`adventure.equipment.ownership.transfer.wizard` (Equipment User+):

1. **From** / **To** partner (defaults from the asset).
2. **Transfer date** — becomes `date_from` on the new row and `date_to` on the closed row.
3. **Reason** — maps to `change_type` (e.g. sale).
4. **Verification state** — copied to the new history row and asset.
5. **Notes** and optional **Source transaction reference**.

Confirm updates `partner_id`, `ownership_verification_state`, and history; an ownership event is logged.

## Verification states

| State | Meaning |
|-------|---------|
| `unverified` | Default; not yet confirmed |
| `pending` | Awaiting staff or document review |
| `verified` | Ownership confirmed |
| `disputed` | Conflict or unclear provenance |

Stored on the asset (`ownership_verification_state`) and on each history row (`verification_state`).

## Company rules

- Asset `company_id` must align with the owner’s `company_id` when the partner is company-specific.
- Ownership rows inherit `company_id` from the asset.
- Multi-company record rules restrict visibility to allowed companies.

## Partner constraint

The owner must belong to the same company as the equipment record when the partner has a `company_id` set.
