# Adventure POS (Odoo)

Custom Odoo 18 stack for retail POS, inventory, and related modules. Custom code lives under `addons/`.

## Quick start

**New developer?** Use the step-by-step guide: [docs/developer-onboarding.md](docs/developer-onboarding.md).

**Need to offload Docker/Odoo/Postgres from your laptop?** Use the remote VM workflow: [docs/remote-development.md](docs/remote-development.md).

1. Copy `.env.example` to `.env` and set variables as needed.
2. Start services: `docker compose up -d` (or `make up`).
3. **Once**, initialize the default DB: `make init-db` (avoids HTTP 500 until `base` is installed).
4. The Postgres database now persists across `docker compose down` / `up`. To intentionally wipe and recreate local dev data, run `make reset-db`.
5. Open [http://localhost:8069](http://localhost:8069) and sign in; install **Adventure Base** from Apps if needed.

Full setup (Cursor, OpenClaw, GitHub, API keys) is documented in [docs/setup.md](docs/setup.md). Agent conventions: [docs/agent-rules.md](docs/agent-rules.md). **Issues, Projects, branches, PRs:** [docs/development-tracking.md](docs/development-tracking.md). **Remote dev VM:** [docs/remote-development.md](docs/remote-development.md). **Shared GCP sandbox** (project, `gcloud` profile, deploy workflow): [docs/shared-environment.md](docs/shared-environment.md). **Cursor → push → sandbox:** [docs/sandbox-cursor-to-deploy.md](docs/sandbox-cursor-to-deploy.md).

## Development Workflow

Follow the branching and pull request rules in [CONTRIBUTING.md](CONTRIBUTING.md). Feature work starts from `develop`, feature PRs target `develop`, and only release or hotfix changes should go to `main`.

## Layout

- `.github/` — Issue & PR templates; [deploy-gcp-sandbox workflow](.github/workflows/deploy-gcp-sandbox.yml) (push to `develop`)
- `addons/` — Odoo modules (`adventure_base`, `adventure_pos`, planned: inventory, customers, purchase, reports)
- `config/` — Tooling config (e.g. OpenClaw)
- `docs/` — Setup and agent guidelines; [development tracking (GitHub Issues)](docs/development-tracking.md); [data model](docs/data-model/core-model.md); [master catalog & sync](docs/architecture/master-catalog-and-sync.md); [tenant provisioning](docs/architecture/tenant-provisioning.md); [FareHarbor booking sync (draft)](docs/integrations/fareharbor-pos-sync.md); [migrations (e.g. Dive Shop 360)](docs/migrations/README.md); [shared environment](docs/shared-environment.md); [sandbox deploy from Cursor](docs/sandbox-cursor-to-deploy.md)
- `scripts/` — Helper scripts (e.g. [gcp-sandbox-vm.ps1](scripts/gcp-sandbox-vm.ps1), [gcp-sandbox-reset-db.ps1](scripts/gcp-sandbox-reset-db.ps1) / [gcp-sandbox-reset-db.sh](scripts/gcp-sandbox-reset-db.sh) for shared sandbox DB wipe; [remote-dev.ps1](scripts/remote-dev.ps1) / [remote-dev.sh](scripts/remote-dev.sh) for developer-owned remote VMs)

Do not store secrets in the repo; use `.env` (ignored by git).
