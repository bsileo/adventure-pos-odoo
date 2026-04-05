# Adventure POS (Odoo)

Custom Odoo 18 stack for retail POS, inventory, and related modules. Custom code lives under `addons/`.

## Quick start

**New developer?** Use the step-by-step guide: [docs/developer-onboarding.md](docs/developer-onboarding.md).

1. Copy `.env.example` to `.env` and set variables as needed.
2. Start services: `docker compose up -d` (or `make up`).
3. Open [http://localhost:8069](http://localhost:8069) and create a database.

Original bootstrap and tooling notes: [docs/setup.md](docs/setup.md). Agent and Git conventions: [docs/agent-rules.md](docs/agent-rules.md).

## Layout

- `addons/` — Odoo modules (`adventure_base`, future modules)
- `config/` — Tooling config (e.g. OpenClaw)
- `docs/` — Setup and agent guidelines
- `scripts/` — Helper scripts

Do not store secrets in the repo; use `.env` (ignored by git).
