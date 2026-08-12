# Agent Workflow

See **[AGENTS.md](AGENTS.md)** for Cursor / cloud agent environment commands, Tidewater bootstrap, and safety rules. Cloud development details: [docs/cursor-cloud-development.md](docs/cursor-cloud-development.md).

- Base all new work on `origin/develop`.
- Never create feature branches from `main`.
- Name new branches `feature/*`, `bugfix/*`, or `hotfix/*` (Cursor cloud agents may use `cursor/…` as required by the cloud environment).
- Open pull requests into `develop` unless explicitly instructed to create a release or hotfix PR.
- Never merge directly into `main`.
