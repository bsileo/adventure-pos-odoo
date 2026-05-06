# Adventure POS (Odoo)

Custom Odoo 19 stack for retail POS, inventory, and related modules. Custom code lives under `addons/`.

## Quick start

**New developer?** Use the step-by-step guide: [docs/developer-onboarding.md](docs/developer-onboarding.md).

**Need to offload Docker/Odoo/Postgres from your laptop?** Use the remote VM workflow: [docs/remote-development.md](docs/remote-development.md).

1. Copy `.env.example` to `.env` and set variables as needed.
2. Start services: `docker compose up -d` (or `make up`).
3. **Once**, initialize the default DB: `make init-db` (installs `base` **without** Odoo demonstration/sample data; avoids HTTP 500 until `base` is installed).
4. The Postgres database now persists across `docker compose down` / `up`. To intentionally wipe and recreate local dev data, run `make reset-db`.
5. Open [http://localhost:8069](http://localhost:8069) and sign in; install **Adventure Base** from Apps if needed.

Full setup (Cursor, OpenClaw, GitHub, API keys) is documented in [docs/setup.md](docs/setup.md). **Agents and developers:** follow [docs/agent-rules.md](docs/agent-rules.md) (including the **documentation-first workflow** before starting a work stream—architecture, data model, integrations, and future design pages). **Issues, Projects, branches, PRs:** [docs/development-tracking.md](docs/development-tracking.md). **Remote dev VM:** [docs/remote-development.md](docs/remote-development.md). **Shared GCP sandbox** (project, `gcloud` profile, deploy workflow): [docs/shared-environment.md](docs/shared-environment.md). **Cursor → push → sandbox:** [docs/sandbox-cursor-to-deploy.md](docs/sandbox-cursor-to-deploy.md).

## Development Workflow

Follow the branching and pull request rules in [CONTRIBUTING.md](CONTRIBUTING.md). Feature work starts from `develop`, feature PRs target `develop`, and only release or hotfix changes should go to `main`.

## Documentation site (MkDocs Material)

**Online docs:** [Event Ops Developer Docs](https://bsileo.github.io/adventure-pos-odoo/) · **Repository:** [bsileo/adventure-pos-odoo](https://github.com/bsileo/adventure-pos-odoo).

Markdown under [`docs/`](docs/) is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). **Pre-production:** pushes to **`develop`** update [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow) via [`.github/workflows/docs.yml`](.github/workflows/docs.yml). Pushes to **`main`** and pull requests targeting `main` or `develop` run a strict build only (no deploy from `main` until you change the workflow).

**Add or edit docs:** edit files under `docs/` (and add new pages to the `nav` section in [`mkdocs.yml`](mkdocs.yml) if you want them in the sidebar).

**Preview locally (Windows PowerShell):**

```powershell
python -m venv .venv-docs
.\.venv-docs\Scripts\Activate.ps1
pip install -r requirements-docs.txt
mkdocs serve
```

Build check (same as CI): `mkdocs build --strict`

**Repo admin:** enable Pages with source **GitHub Actions** (Settings → Pages). For private repos, confirm org policy for who can view Pages.

If the **Documentation** workflow’s deploy job fails with **HTTP 404** / “Failed to create deployment”, Pages is still set to **Deploy from a branch** or Pages is disabled. Switch **Build and deployment → Source** to **GitHub Actions**, save, then re-run the failed workflow or push an empty commit to `develop`.

## Layout

- `.github/` — Issue & PR templates; [deploy-gcp-sandbox workflow](.github/workflows/deploy-gcp-sandbox.yml) (push to `develop`); [documentation workflow](.github/workflows/docs.yml) (MkDocs build; Pages deploy from `develop`)
- `addons/` — Odoo modules (`adventure_base`, `adventure_pos`, planned: inventory, customers, purchase, reports); third-party App Store modules: [addons/README.md](addons/README.md)
- `config/` — Tooling config (e.g. OpenClaw)
- `docs/` — Setup and agent guidelines; [documentation-first workflow](docs/agent-rules.md#documentation-first-workflow-mandatory); [development tracking (GitHub Issues)](docs/development-tracking.md); [data model](docs/data-model/core-model.md); [master catalog & sync](docs/architecture/master-catalog-and-sync.md); [tenant provisioning](docs/architecture/tenant-provisioning.md); [scuba training & scheduling **(future design)**](docs/architecture/scuba-training-scheduling.md); [FareHarbor booking sync (draft)](docs/integrations/fareharbor-pos-sync.md); [migrations (e.g. Dive Shop 360)](docs/migrations/README.md); [shared environment](docs/shared-environment.md); [sandbox deploy from Cursor](docs/sandbox-cursor-to-deploy.md)
- `scripts/` — Helper scripts (e.g. [gcp-sandbox-vm.ps1](scripts/gcp-sandbox-vm.ps1), [gcp-sandbox-reset-db.ps1](scripts/gcp-sandbox-reset-db.ps1) / [gcp-sandbox-reset-db.sh](scripts/gcp-sandbox-reset-db.sh) for shared sandbox DB wipe; [remote-dev.ps1](scripts/remote-dev.ps1) / [remote-dev.sh](scripts/remote-dev.sh) for developer-owned remote VMs)

Do not store secrets in the repo; use `.env` (ignored by git).
