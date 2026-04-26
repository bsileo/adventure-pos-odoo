# Developer onboarding — Adventure POS (Cursor)

Step-by-step setup for a new developer using **[Cursor](https://cursor.com)** as the IDE. You will run **Odoo 18** and **PostgreSQL** with Docker, work from a local clone in Cursor, and keep secrets (especially **`.env`**) off git and out of shared AI transcripts where possible.

If your laptop is resource-constrained and you want Docker, Odoo, and Postgres to run on a **developer-owned GCP VM** instead, use [remote-development.md](remote-development.md). That path is designed for **Cursor Remote SSH** and keeps the shared sandbox separate.

---

## Before you start

Install and sign into **Cursor** on your machine. This guide applies to **Windows and macOS** (Linux is fine too if Docker runs there). Confirm you also have:

| Requirement | Notes |
|-------------|--------|
| **Git** | Used from a terminal (Cursor’s integrated terminal or any other) for clone, pull, and branches. For a **private** repo, set up GitHub auth first (HTTPS with a [credential helper / PAT](https://docs.github.com/en/get-started/git-basics/set-up-git), **SSH** with a key added to GitHub, or `gh auth login`). **Clone repo** in Cursor still uses your normal Git credentials. |
| **Docker Desktop** (or compatible engine) | Install it, start it, and wait until it reports **running** before `docker compose`. If `docker compose` errors with *Cannot connect to the Docker daemon* (or similar), the engine isn’t running yet. **Windows:** prefer the **WSL2** backend if Docker prompts you. **macOS:** use Docker Desktop for Mac (Apple Silicon or Intel per Docker’s install page). Skip this if you are following [remote-development.md](remote-development.md) and plan to run Docker on a GCP VM instead. |

Optional:

- **OpenClaw** and an **OpenAI API key** if you use that workflow alongside Cursor.
- **GitHub CLI (`gh`)** in a terminal for auth and PRs.

On **macOS**, install **`make`** if you use the `make up` / `make init-db` shortcuts (e.g. `xcode-select --install` for Apple’s build tools, or `brew install make` and use `gmake` if your PATH differs).

---

## 1. Open the repo in Cursor

Pick any of these; the goal is the same: the opened folder should be the repo **root** (where `docker-compose.yml` lives). You do **not** have to use Cursor to clone—**Option C** is fine if you already use another Git client.

### Option A — Welcome screen **Clone repo**

1. Open Cursor (or **File → New Window** for a fresh welcome screen).
2. Choose **Clone repo** (folder-with-download icon on the welcome page).
3. When prompted for the URL, use:

   `https://github.com/bsileo/adventure-pos-odoo.git`

   (Use your fork’s URL if you develop from a fork.)
4. Choose a parent directory when asked; Cursor clones and opens the project.
5. If Cursor asks to **trust** the workspace, trust it so tasks, terminals, and rules behave normally.

### Option B — Clone from Cursor’s integrated terminal

1. In Cursor: **Terminal → New Terminal** (or **Ctrl+`** on Windows/Linux, **Cmd+`** on macOS, or **View → Terminal**).
2. `cd` to where you keep projects, then clone:

   ```bash
   git clone https://github.com/bsileo/adventure-pos-odoo.git
   cd adventure-pos-odoo
   ```

3. **File → Open Folder…** and choose the `adventure-pos-odoo` folder you just cloned (the repo **root**, where `docker-compose.yml` lives).
4. If Cursor asks to **trust** the workspace, trust it so tasks, terminals, and rules behave normally.

### Option C — Clone outside Cursor, then open the folder

1. Clone wherever you prefer (examples):
   - **macOS Terminal**, **Linux shell**, **PowerShell**, or **Git Bash** (any directory): same `git clone` / `cd` commands as in Option B.
   - **GitHub Desktop** or another GUI: clone the repo to disk as you usually would.
2. In Cursor: **File → Open Folder…** → choose the repo root (`adventure-pos-odoo`, the folder that contains `docker-compose.yml`).

### Git branches (in Cursor)

Use the **Source Control** view (sidebar icon) or the terminal:

```bash
git checkout develop
git pull origin develop
git checkout -b feat/42-your-short-description
```

Include the **GitHub issue number** in the branch name when there is a tracking issue (example: `feat/42-line-item-notes`). If there is no issue yet, create one ([development tracking](development-tracking.md)) or use a temporary name and rename after filing the issue.

If **`develop` does not exist** on the remote (e.g. the team uses only `main`), run `git branch -r` to see remote branches, check with the team which branch to branch from, then `git checkout <that-branch>` and `git pull` before creating your feature branch.

Don’t commit directly to `main`. Conventions: [agent-rules.md — Git workflow](agent-rules.md#git-workflow), [development-tracking.md](development-tracking.md) (PRs must link issues with `Closes #…`).

---

## 2. Environment variables — working with `.env` in Cursor

`.env` holds local secrets (e.g. **OpenAI**). It is **gitignored**; only **`.env.example`** is in the repo.

### Create `.env` from the template

1. In the **Explorer** sidebar, open **`.env.example`** and skim the comments.
2. Copy it to **`.env`** using whichever you prefer:
   - **Explorer:** Right-click `.env.example` → **Copy**, then paste in the same folder and rename to `.env`, **or**
   - **Terminal** (repo root):

     ```bash
     cp .env.example .env
     ```

     Windows PowerShell:

     ```powershell
     Copy-Item .env.example .env
     ```

### Edit `.env` in the editor

1. Open **`.env`** from Explorer (Cursor may hide some ignored files depending on settings; if you don’t see it, use **File → Open File…** and pick `.env`, or create it next to `.env.example`).
2. Set values as plain **`KEY=...`** lines (no quotes unless your value needs them). Example:

   ```env
   OPENAI_API_KEY=sk-...
   ```

   Get keys from [OpenAI API keys](https://platform.openai.com/api-keys).

3. Save the file (**Ctrl+S** on Windows/Linux, **Cmd+S** on macOS). Other tools (OpenClaw, some extensions) often load `.env` from the **project root** when their process starts from that folder—restart terminals or the gateway after changing `.env` if something doesn’t pick up the new value.

### Keep secrets off git (use Source Control)

1. Open **Source Control** (sidebar).
2. Confirm **`.env` never appears** in the “Changes” list to be staged. Only **`.env.example`** should be committed when you intentionally change the template.
3. If `.env` ever shows as tracked, **do not commit it**—ask the team; you may need to remove it from the index once (`git rm --cached .env`) while keeping the local file.

### Cursor Agent / chat and `.env`

- **Do not paste real API keys** into Cursor chat if your workspace or logging might sync or be shared. Prefer editing `.env` locally and describing the *step* (“I set `OPENAI_API_KEY` in `.env`”) without the secret.
- If you use **Agent** mode for setup help, you can reference **`.env.example`** and **`docker-compose.yml`** with **`@`** in the prompt so the model sees the shape of config, not your actual `.env`.

### Optional: OS user environment for API keys

**Windows (PowerShell)** — persistent user variable:

```powershell
setx OPENAI_API_KEY "your-key-here"
```

**macOS / Linux** — add to `~/.zshrc` or `~/.bashrc` (example):

```bash
export OPENAI_API_KEY="your-key-here"
```

Open a **new** terminal (or restart Cursor) so new processes see the variable.

---

## 3. Integrated terminal — Docker

Always open the terminal **in the repo root** (Cursor usually does this for new terminals; check the path in the prompt).

1. Start **Docker Desktop** (or your daemon).
2. In Cursor’s terminal:

   ```bash
   docker compose up -d
   ```

   Or run **`make up`** if `make` is on your PATH.

3. Check services:

   ```bash
   docker compose ps
   ```

You should see **`db`** (Postgres 16) and **`odoo`** (`odoo:18.0`).

**Ports:** **8069** (Odoo), **5432** (Postgres on the host). If something else is using them, stop that process or change ports with the team.

To see **what is listening** (examples):

- **macOS / Linux:** `lsof -i :8069` and `lsof -i :5432` (or `sudo` if nothing shows and you expect a listener).
- **Windows (PowerShell or cmd):** `netstat -ano | findstr :8069` and the same with `:5432` (or **Resource Monitor → Network**).

**Logs / stop:**

```bash
docker compose logs -f odoo
docker compose down
```

### First boot: `Internal Server Error` on http://localhost:8069/

Postgres creates an empty database named **`odoo`**. The Odoo container connects to it before any modules are installed, so **`/`** can return **500** until the DB is initialized.

**Fix (run once after the first `docker compose up -d`):**

```bash
make init-db
```

Or the same command without `make`:

```bash
docker compose exec odoo odoo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo -d odoo -i base --without-demo=all --stop-after-init
```

That installs **`base`** (and core web stack) into database **`odoo`** **without** Odoo demonstration/sample data (`--without-demo=all`). Then reload **http://localhost:8069/** — you should get the normal Odoo UI / login instead of 500.

To confirm in logs: `docker compose logs odoo` should no longer show `Database odoo not initialized` or `relation "ir_module_module" does not exist`.

---

## 4. First-time Odoo setup

1. Complete **section 3** (Docker up) and, if needed, **`make init-db`** from the note above.
2. Open **http://localhost:8069** in your normal browser (or Cursor’s Simple Browser if you use it).
3. **Sign in** to database **`odoo`** (credentials set when `base` was installed; the default internal user is often **Login:** `admin` / **Password:** `admin` until you change it under **Settings → Users**). If login fails, use **Manage databases** (`/web/database/manager`) or ask the team—do not commit real passwords to the repo.
4. Enable **Developer Mode** when available (Settings → Developer Tools) for easier technical menus.
5. **Apps → Update Apps List** → search **Adventure Base** → **Install** `adventure_base`.
6. For MVP POS work: ensure **Point of Sale** is available (installed or will be pulled in as a dependency), then **Install** `adventure_pos` (**Adventure POS**).

**Optional — extra database via the UI:** If you prefer a separate DB (e.g. `adventure_dev`), use **Manage databases** to create it; that flow sets master password and admin user in the browser. Leave **Load demonstration data** unchecked to match **`make init-db`** (no sample data). The default Postgres DB name in `docker-compose.yml` is still **`odoo`** unless you change team defaults.

Custom addons: **`./addons`** in the repo → **`/mnt/extra-addons`** in the container. After Python/manifest changes, restart Odoo or **upgrade** the module from the UI.

The local Compose Postgres data persists in a Docker volume, so `docker compose down` no longer wipes the Odoo database by default. If you intentionally want a clean local database, run **`make reset-db`** to remove the Compose volume, restart the stack, and reinstall `base`.

---

## 5. Configuration as code (repeatable Odoo settings)

Anything you change in the Odoo UI that the team **intends to keep** for **every** environment (local, test, staging, production) or for **every new developer** after install should not live only in one database.

**Default workflow**

1. Decide the setting or master data in the UI if that helps you learn Odoo.
2. **Replicate it in git**: add or update **module `data/`** (XML/CSV), hooks in `__manifest__.py`, or a **checked-in script** under `scripts/` (or similar) if XML is impractical.
3. Open a PR that includes those files so the next `docker compose` + module install/upgrade or Odoo.sh deploy reproduces the same result.

Spikes and one-off experiments are fine on a throwaway database; before the work is **merged** or called “official,” capture the agreed configuration in the repo. **Agents** follow the same rule: see [agent-rules.md — Configuration as code](agent-rules.md#4-configuration-as-code-mandatory-for-agreed-odoo-settings).

**Why:** Manual-only configuration drifts between machines, blocks onboarding, and cannot be applied consistently to test/stage/prod.

---

## 6. Daily work in Cursor

| Topic | What to use |
|--------|-------------|
| **Project rules** | `.cursor/rules/` (`odoo.mdc`, `repo.mdc`) — align with [agent-rules.md](agent-rules.md). Cursor loads them per rule settings (paths/globs). |
| **Context** | In chat, **`@`**-mention files (e.g. `@docs/agent-rules.md`, `@addons/adventure_base/__manifest__.py`) instead of pasting large snippets. |
| **Odoo / Python** | Install the **Python** extension in Cursor if you want analysis, go-to-definition, and formatting in `addons/`. |
| **Docker** | Optional **Docker** extension to see compose services; same images as `docker compose ps`. |

### Development tracking (GitHub Issues)

Work is tracked with **GitHub Issues** and a **GitHub Project** board. Use an issue per feature or bug, branch names that include the issue number, and **`Closes #123`** in the PR body so the issue closes on merge. Full workflow, labels, and optional **`gh`** / Cursor tips: **[development-tracking.md](development-tracking.md)**.

---

## 7. OpenClaw (optional, beside Cursor)

- **Cursor** uses repo rules and your chosen models in the product settings.
- **OpenClaw** stores global config under **`~/.openclaw/`** (macOS/Linux) or **`%USERPROFILE%\.openclaw\`** (Windows) by default. Point its **workspace** at this **repo root** so file tools match your tree; align model config with **`config/openclaw.json5`** if your team uses that snippet.

Never store keys in tracked files—**`.env`** or OS env only.

---

## 8. Verify you are ready

- [ ] Repo opened in Cursor as a **folder** (root contains `docker-compose.yml`).
- [ ] **`.env`** exists, keys filled as needed, and **`.env` is not** staged in Source Control.
- [ ] `docker compose ps` in Cursor’s terminal shows **`db`** and **`odoo`**.
- [ ] http://localhost:8069 works; **Adventure Base** and **Adventure POS** installed (or you know how to install them).
- [ ] You’re on a **feature branch** from the team’s integration branch (**`develop`** if your remote has it—see **Git branches** above) for product changes, and you know how work links to **[GitHub Issues](development-tracking.md)** (issue → branch → PR → `Closes #…`).
- [ ] You understand **configuration as code** ([section 5](#5-configuration-as-code-repeatable-odoo-settings)): agreed Odoo settings belong in the repo, not only in your local DB.

---

## Reference and history

- **[README.md](../README.md)** — Short overview.
- **[remote-development.md](remote-development.md)** — Run Docker, Odoo, and Postgres on your own GCP dev VM with Cursor Remote SSH.
- **[sandbox-cursor-to-deploy.md](sandbox-cursor-to-deploy.md)** — Push to `develop` and verify the **shared GCP sandbox** (start VM, PR flow, Actions).
- **[development-tracking.md](development-tracking.md)** — GitHub Issues, Projects, branches, PRs, labels.
- **[agent-rules.md](agent-rules.md)** — Modules, Git, security, POS/inventory expectations.
- **[setup.md](setup.md)** — Original greenfield checklist; **clone-based** onboarding is this document.

If setup or Cursor workflows change, update **this file** in the same PR.
