# Adventure POS (Odoo)

Custom Odoo 18 stack for retail POS, inventory, and related modules. Custom code lives under `addons/`.

## Quick start

1. Copy `.env.example` to `.env` and set variables as needed.
2. Start services: `docker compose up -d` (or `make up`).
3. Open [http://localhost:8069](http://localhost:8069) and create a database.

Full setup (Cursor, OpenClaw, GitHub, API keys) is documented in [docs/setup.md](docs/setup.md).

## Layout

- `addons/` — Odoo modules (`adventure_base`, future modules)
- `config/` — Tooling config (e.g. OpenClaw)
- `docs/` — Setup and agent guidelines
- `scripts/` — Helper scripts

Do not store secrets in the repo; use `.env` (ignored by git).
