# Adventure POS (Odoo)

Custom Odoo 18 stack for retail POS, inventory, and related modules. Custom code lives under `addons/`.

## Quick start

**New developer?** Use the step-by-step guide: [docs/developer-onboarding.md](docs/developer-onboarding.md).

1. Copy `.env.example` to `.env` and set variables as needed.
2. Start services: `docker compose up -d` (or `make up`).
3. **Once**, initialize the default DB: `make init-db` (avoids HTTP 500 until `base` is installed).
4. Open [http://localhost:8069](http://localhost:8069) and sign in; install **Adventure Base** from Apps if needed.

Full setup (Cursor, OpenClaw, GitHub, API keys) is documented in [docs/setup.md](docs/setup.md). Agent conventions: [docs/agent-rules.md](docs/agent-rules.md). **Issues, Projects, branches, PRs:** [docs/development-tracking.md](docs/development-tracking.md). **Shared GCP sandbox** (project, `gcloud` profile): [docs/shared-environment.md](docs/shared-environment.md).

## Layout

- `.github/` — Issue & PR templates for GitHub
- `addons/` — Odoo modules (`adventure_base`, `adventure_pos`, planned: inventory, customers, purchase, reports)
- `config/` — Tooling config (e.g. OpenClaw)
- `docs/` — Setup and agent guidelines; [development tracking (GitHub Issues)](docs/development-tracking.md); [data model](docs/data-model/core-model.md); [master catalog & sync](docs/architecture/master-catalog-and-sync.md); [tenant provisioning](docs/architecture/tenant-provisioning.md); [FareHarbor booking sync (draft)](docs/integrations/fareharbor-pos-sync.md); [migrations (e.g. Dive Shop 360)](docs/migrations/README.md); [shared environment](docs/shared-environment.md)
- `scripts/` — Helper scripts

Do not store secrets in the repo; use `.env` (ignored by git).
