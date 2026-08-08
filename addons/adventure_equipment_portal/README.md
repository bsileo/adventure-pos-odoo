# Adventure Equipment Portal

Customer self-service for `adventure.equipment.asset` on Odoo Website / Portal.

## Features (MVP)

- `/my/equipment` — list owned gear
- `/my/equipment/<id>` — detail (read-only serial/category/verification)
- `/my/equipment/<id>/edit` — nickname + customer notes
- `/my/equipment/register` — customer-reported registration (pending verification)
- Portal ACL + partner-scoped record rules (single owner, company-aware)

## Install

Depends on `adventure_equipment` and `adventure_website`.

## Tidewater demo

Seed creates portal users (password `TidewaterDemo1!`):

| Login | Partner |
|-------|---------|
| `certified_current@example.test` | Certified current diver |
| `nitrox@example.test` | Nitrox diver |
| `uncertified@example.test` | Uncertified customer |

Equipment assets for those partners come from `adventure_equipment_scuba` Tidewater seed.

See [seed-data.md](../../docs/seed-data.md) and [client-web-portal.md](../../docs/architecture/client-web-portal.md).
