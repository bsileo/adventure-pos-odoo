# AGENTS.md — Adventure POS (Cursor / cloud agents)

Repository-specific guidance for AI agents working in this codebase. Humans: see also [docs/agent-rules.md](docs/agent-rules.md) and [docs/cursor-cloud-development.md](docs/cursor-cloud-development.md).

## What this repo is

- **Odoo 19** custom stack (**Adventure POS**) with modules under `addons/`.
- Runtime: **Docker Compose** (`odoo` + **PostgreSQL 16**).
- Canonical development/demo tenant: **Tidewater Dive Shop** (Pittsburgh, fictional). See [docs/seed-data.md](docs/seed-data.md).

## Prefer Cursor cloud agents

Primary development and testing should happen in **Cursor cloud agents** with an isolated Docker stack on the VM. Use the same Make/script commands locally when needed.

**Do not** use production databases, real customer data, or the shared GCP sandbox unless a human explicitly asks for sandbox work. Default cloud work is **local-to-the-VM** Compose + Tidewater seed.

## One command set (local = cloud)

| Goal | Command |
|------|---------|
| Setup (Docker, `.env`, up, init DB, Tidewater seed) | `make setup` |
| Start stack | `make start` |
| Reset DB + reseed Tidewater | `make reset` (non-interactive: `make reset ASSUME_YES=1`) |
| Run module tests | `make test` |
| Smoke validate (login + POS) | `make validate` |
| Seed only (idempotent) | `make seed-tidewater` |

Scripts live under `scripts/` (`dev-setup.sh`, `dev-start.sh`, `dev-reset.sh`, `dev-test.sh`, `dev-validate.sh`). Cursor cloud hooks: `scripts/cursor-cloud-install.sh` / `scripts/cursor-cloud-start.sh` via [`.cursor/environment.json`](.cursor/environment.json).

## Disposable login

After `make setup` / cloud start on a fresh DB:

- URL: http://127.0.0.1:8069
- Database: `odoo`
- Login / password: **`admin` / `admin`** (Odoo default until changed)

Do not commit real passwords. Optional integrations (`OPENAI_API_KEY`, `SMARTWAIVER_API_KEY`) are merged into `.env` when present as environment / Cursor Cloud Secrets; they are **not** required for Tidewater bootstrap today.

## Browser validation

After the stack is up:

1. **A)** Sign in and confirm **Tidewater Dive Shop** branding/company.
2. **C)** Open **Point of Sale**, select a POS config, and open/start a session when reviewing UI.

Keep the development server / Compose stack **running** when human review is useful (`make start` / cloud `start` attaches to logs).

Automated API smoke: `make validate`.

## Tests

Prefer scoped tags while iterating:

```bash
make test TEST_TAGS=/adventure_equipment
# or
bash ./scripts/dev-test.sh --tags /adventure_waiver,/adventure_smartwaiver
```

Default `make test` runs tags for modules that currently ship tests.

## Git workflow

- Base work on `origin/develop` (not `main`).
- Feature PRs target `develop`.
- Cloud agent branches use `cursor/<descriptive-name>-…` as required by the cloud environment.
- Humans: prefer `feature/*`, `bugfix/*`, `hotfix/*` per [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) / [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation-first

Before a work stream, read [docs/agent-rules.md](docs/agent-rules.md) and skim relevant architecture / data-model / integrations pages (including **future** labels). New user-visible features need **module-owned Tidewater seed** coverage in the same change train.

## Ignore

- **`backup.sql`** at repo root — do **not** restore it for development; use `make setup` / Tidewater seed only.
- Shared GCP sandbox scripts (`scripts/gcp-sandbox-*.sh`) — only when a human explicitly requests sandbox operations.

## Protect production

Never point Compose or seeds at production. Never commit `.env` or API keys. Use development/mock/sandbox integrations only.
