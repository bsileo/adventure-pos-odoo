# Adventure Website

Thin Odoo Website + Portal shell for AdventurePOS (pattern A: Odoo-hosted shop site).

## What it does

- Installs/depends on `website`, `portal`, and `auth_signup`
- Enables **open self-signup** (`auth_signup.invitation_scope = b2c`)
- Replaces the default homepage with a **minimal** branded page: company name, Sign in / Sign up, and links to My Account / My Equipment
- Uses the **default** Website theme plus `res.company` logo/colors (no App Store theme required)

## What it does not do

- Equipment domain UX — see `adventure_equipment_portal`
- Rich marketing pages / content migration
- Customer profile editing (separate workstream)

## Architecture

See [Client web portal](../../docs/architecture/client-web-portal.md).
