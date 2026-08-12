# Cursor cloud development

Primary development and testing for Adventure POS should use **Cursor cloud agents** with an isolated Docker Compose stack on each VM. Local laptops and [developer-owned remote VMs](remote-development.md) use the **same** Make targets.

Published docs: [Event Ops Developer Docs](https://bsileo.github.io/adventure-pos-odoo/).

## Architecture (cloud VM)

| Piece | Choice |
|-------|--------|
| App | Odoo **19** (`Dockerfile` / `adventure-pos-odoo:19.0`) |
| DB | PostgreSQL **16** in Compose (volume local to the VM) |
| Dataset | **Tidewater Dive Shop** via `make setup` / `make seed-tidewater` |
| Shared GCP sandbox | **Out of bounds by default** — only when a human explicitly requires it |

Each cloud agent VM gets its own Postgres data. Do not point agents at production or at the shared sandbox database for normal feature work.

## Commands

| Goal | Command |
|------|---------|
| Full setup | `make setup` |
| Start | `make start` |
| Reset + Tidewater | `make reset` / `make reset ASSUME_YES=1` |
| Tests | `make test` |
| Smoke validate | `make validate` |

Cursor environment hooks ([`.cursor/environment.json`](../.cursor/environment.json)):

- **install** → `bash ./scripts/cursor-cloud-install.sh` (Docker, `.env`, image build; terminates)
- **start** → `bash ./scripts/cursor-cloud-start.sh` (setup + attach to Compose logs)

Agent instructions: [AGENTS.md](../AGENTS.md).

## Login (disposable DB)

- http://127.0.0.1:8069 — database `odoo`
- **`admin` / `admin`** after fresh `init-db` unless you changed it

## Browser checks

1. Sign in and confirm **Tidewater Dive Shop**.
2. Open **Point of Sale**, pick a POS config, open/start a session when reviewing UI.

Leave Compose running for human review (`start` keeps logs attached in cloud).

## Secrets (optional)

Not required for Tidewater bootstrap today. When you enable integrations, set Cursor Cloud Secrets (or export env vars before setup); `scripts/ensure-dotenv.sh` merges them into local `.env` (gitignored):

| Secret | Purpose |
|--------|---------|
| `OPENAI_API_KEY` | Optional OpenClaw / OpenAI workflows |
| `SMARTWAIVER_API_KEY` | Optional `adventure_smartwaiver` connector |
| `POSTGRES_PASSWORD` | Override Compose DB password (default from `.env.example` is fine for disposable VMs) |

Never commit `.env` or real production credentials.

## Ignore

- Repo-root **`backup.sql`** — do not restore for development; use Tidewater seed only.
- GCP sandbox scripts — only on explicit human request ([shared-environment.md](shared-environment.md)).

## Worktrees

[`.cursor/worktrees.json`](../.cursor/worktrees.json) copies `.env` when possible and ensures Docker is available for isolated local worktrees. Still run `make setup` (or `make start`) in the worktree as needed.
