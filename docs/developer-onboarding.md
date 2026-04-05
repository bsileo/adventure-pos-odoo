# Developer onboarding — Adventure POS

Step-by-step setup for a new developer joining this project. You will run **Odoo 18** and **PostgreSQL** with Docker, work from a local clone of the repo, and keep secrets out of git.

---

## Before you start

Confirm you have:

| Requirement | Notes |
|-------------|--------|
| **Git** | For clone, pull, and branches. |
| **Docker Desktop** (or compatible engine) | Must be running before `docker compose`. On Windows, use WSL2 backend if prompted. |
| **A code editor** | VS Code or Cursor; optional but recommended. |

Optional, depending on your role:

- **OpenClaw** and an **OpenAI API key** if you use the local assistant workflow.
- **GitHub CLI (`gh`)** if you prefer it for auth and PRs.

---

## 1. Clone the repository

```bash
git clone https://github.com/bsileo/adventure-pos-odoo.git
cd adventure-pos-odoo
```

If you use SSH or a fork, use that remote URL instead.

Checkout the integration branch when starting feature work:

```bash
git checkout develop
git pull origin develop
```

Create a **feature branch** from `develop` (do not commit directly to `main`). Example:

```bash
git checkout -b feature/your-short-description
```

See [Agent rules — Git workflow](agent-rules.md#git-workflow) for conventions.

---

## 2. Environment variables

1. Copy the example file:

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell (same folder):

   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env`:

   - Set **`OPENAI_API_KEY`** if you use OpenAI-backed tools (OpenClaw, some editor integrations). Get a key from [OpenAI API keys](https://platform.openai.com/api-keys).
   - Other variables match Docker Postgres and Odoo defaults used by `docker-compose.yml`; change them only if you are avoiding port conflicts or aligning with team standards.

3. **Never commit `.env`.** It is listed in `.gitignore`.

Optional — user-wide Windows environment (new terminals required after this):

```powershell
setx OPENAI_API_KEY "your-key-here"
```

---

## 3. Start the stack with Docker

1. Start Docker Desktop (or your Docker daemon).
2. From the **repository root** (where `docker-compose.yml` lives):

   ```bash
   docker compose up -d
   ```

   Or: `make up` if you have `make` available.

3. Check containers:

   ```bash
   docker compose ps
   ```

You should see **`db`** (Postgres 16) and **`odoo`** (image `odoo:18.0`) running.

**Ports:**

- **8069** — Odoo web UI  
- **5432** — Postgres (exposed to the host; stop any local Postgres using the same port, or adjust the compose file with team agreement)

To view logs:

```bash
docker compose logs -f odoo
```

To stop:

```bash
docker compose down
```

---

## 4. First-time Odoo setup

1. Open **http://localhost:8069** in a browser.

2. On the database manager:

   - Create a **database** (e.g. `adventure_dev`).
   - Set **master password** (store it safely; used for database management).
   - Choose **Language**, **Country**, and an **admin email/password** for the Odoo user.

3. After login, enable **Developer Mode** (Settings → scroll to Developer Tools → Activate Developer Mode), if your Odoo build exposes it, so apps and technical menus are easier to find.

4. Install the custom base module:

   - **Apps** → **Update Apps List**
   - Remove the “Apps” filter if needed, search for **Adventure Base**
   - **Install** `adventure_base`

Custom addons are mounted from the repo at `./addons` → `/mnt/extra-addons` in the container. After you change Python or manifest files, **restart the Odoo container** or **upgrade the module** from the UI as you normally would in Odoo.

---

## 5. Project layout (where things live)

| Path | Purpose |
|------|--------|
| `addons/` | All custom Odoo modules; **do not** change Odoo core. |
| `config/` | Tooling such as optional OpenClaw config reference (`openclaw.json5`). |
| `docs/` | Setup notes, agent rules, this onboarding doc. |
| `scripts/` | Helper scripts (add as needed). |
| `.cursor/rules/` | Cursor agent rules aligned with [agent-rules.md](agent-rules.md). |

---

## 6. AI assistants and OpenClaw (optional)

- **Cursor:** Rules in `.cursor/rules/` are loaded according to Cursor’s rule settings.
- **OpenClaw:** Configuration lives globally under `%USERPROFILE%\.openclaw\` by default. Point OpenClaw’s **workspace** at this repo root so file tools and context match the project, and merge model/provider settings with the example in `config/openclaw.json5` if you use that layout. See your OpenClaw docs for `agents.defaults.workspace` and `OPENCLAW_CONFIG_PATH`.

Do **not** put API keys in tracked files; use `.env` or OS/user environment variables.

---

## 7. Verify you are ready

- [ ] `docker compose ps` shows `db` and `odoo` healthy or running.
- [ ] http://localhost:8069 loads and you can log into your dev database.
- [ ] **Adventure Base** is installed (or you know how to install it from Apps).
- [ ] `.env` exists locally with `OPENAI_API_KEY` if you need it; `.env` is not in `git status`.
- [ ] You are on a **feature branch** from `develop` for code changes.

---

## Reference and history

- **[README.md](../README.md)** — Short overview and commands.
- **[agent-rules.md](agent-rules.md)** — How agents and humans should work in this repo (modules, Git, security).
- **[setup.md](setup.md)** — Original “greenfield” bootstrap checklist (historical); **new developers should follow this onboarding doc** for a clone-based workflow.

If setup steps change, update **this file** and mention it in the PR.
