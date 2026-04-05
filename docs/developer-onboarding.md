# Developer onboarding — Adventure POS (Cursor)

Step-by-step setup for a new developer using **[Cursor](https://cursor.com)** as the IDE. You will run **Odoo 18** and **PostgreSQL** with Docker, work from a local clone in Cursor, and keep secrets (especially **`.env`**) off git and out of shared AI transcripts where possible.

---

## Before you start

Install and sign into **Cursor** on your machine. Confirm you also have:

| Requirement | Notes |
|-------------|--------|
| **Git** | Used from Cursor’s integrated terminal for clone, pull, and branches. |
| **Docker Desktop** (or compatible engine) | Running before `docker compose`. On Windows, prefer the WSL2 backend if Docker prompts you. |

Optional:

- **OpenClaw** and an **OpenAI API key** if you use that workflow alongside Cursor.
- **GitHub CLI (`gh`)** in a terminal for auth and PRs.

---

## 1. Open the repo in Cursor

### Option A — Clone from Cursor’s terminal

1. In Cursor: **Terminal → New Terminal** (or `` Ctrl+` `` / **View → Terminal**).
2. `cd` to where you keep projects, then clone:

   ```bash
   git clone https://github.com/bsileo/adventure-pos-odoo.git
   cd adventure-pos-odoo
   ```

3. **File → Open Folder…** and choose the `adventure-pos-odoo` folder you just cloned (the repo **root**, where `docker-compose.yml` lives).
4. If Cursor asks to **trust** the workspace, trust it so tasks, terminals, and rules behave normally.

### Option B — You already cloned outside Cursor

**File → Open Folder…** → select the repo root (`adventure-pos-odoo`).

### Git branches (in Cursor)

Use the **Source Control** view (sidebar icon) or the terminal:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-short-description
```

Don’t commit directly to `main`. Conventions: [agent-rules.md — Git workflow](agent-rules.md#git-workflow).

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

3. Save the file (**Ctrl+S**). Other tools (OpenClaw, some extensions) often load `.env` from the **project root** when their process starts from that folder—restart terminals or the gateway after changing `.env` if something doesn’t pick up the new value.

### Keep secrets off git (use Source Control)

1. Open **Source Control** (sidebar).
2. Confirm **`.env` never appears** in the “Changes” list to be staged. Only **`.env.example`** should be committed when you intentionally change the template.
3. If `.env` ever shows as tracked, **do not commit it**—ask the team; you may need to remove it from the index once (`git rm --cached .env`) while keeping the local file.

### Cursor Agent / chat and `.env`

- **Do not paste real API keys** into Cursor chat if your workspace or logging might sync or be shared. Prefer editing `.env` locally and describing the *step* (“I set `OPENAI_API_KEY` in `.env`”) without the secret.
- If you use **Agent** mode for setup help, you can reference **`.env.example`** and **`docker-compose.yml`** with **`@`** in the prompt so the model sees the shape of config, not your actual `.env`.

### Optional: Windows user env (`setx`)

For tools that only read the OS user environment (not `.env`), run in **PowerShell** (outside or inside Cursor):

```powershell
setx OPENAI_API_KEY "your-key-here"
```

Open a **new** terminal (or restart Cursor) so new processes see it.

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

**Ports:** **8069** (Odoo), **5432** (Postgres on the host). Free those ports or adjust compose with the team.

**Logs / stop:**

```bash
docker compose logs -f odoo
docker compose down
```

---

## 4. First-time Odoo setup

1. Open **http://localhost:8069** in your normal browser (or Cursor’s Simple Browser if you use it).
2. Create a **database** (e.g. `adventure_dev`), set the **master password**, language, country, and **admin** credentials.
3. Enable **Developer Mode** when available (Settings → Developer Tools) for easier technical menus.
4. **Apps → Update Apps List** → search **Adventure Base** → **Install** `adventure_base`.

Custom addons: **`./addons`** in the repo → **`/mnt/extra-addons`** in the container. After Python/manifest changes, restart Odoo or **upgrade** the module from the UI.

---

## 5. Daily work in Cursor

| Topic | What to use |
|--------|-------------|
| **Project rules** | `.cursor/rules/` (`odoo.mdc`, `repo.mdc`) — align with [agent-rules.md](agent-rules.md). Cursor loads them per rule settings (paths/globs). |
| **Context** | In chat, **`@`**-mention files (e.g. `@docs/agent-rules.md`, `@addons/adventure_base/__manifest__.py`) instead of pasting large snippets. |
| **Odoo / Python** | Install the **Python** extension in Cursor if you want analysis, go-to-definition, and formatting in `addons/`. |
| **Docker** | Optional **Docker** extension to see compose services; same images as `docker compose ps`. |

---

## 6. OpenClaw (optional, beside Cursor)

- **Cursor** uses repo rules and your chosen models in the product settings.
- **OpenClaw** uses global config under `%USERPROFILE%\.openclaw\` by default. Point its **workspace** at this **repo root** so file tools match your tree; align model config with **`config/openclaw.json5`** if your team uses that snippet.

Never store keys in tracked files—**`.env`** or OS env only.

---

## 7. Verify you are ready

- [ ] Repo opened in Cursor as a **folder** (root contains `docker-compose.yml`).
- [ ] **`.env`** exists, keys filled as needed, and **`.env` is not** staged in Source Control.
- [ ] `docker compose ps` in Cursor’s terminal shows **`db`** and **`odoo`**.
- [ ] http://localhost:8069 works; **Adventure Base** installed (or you know how to install it).
- [ ] You’re on a **feature branch** from **`develop`** for product changes.

---

## Reference and history

- **[README.md](../README.md)** — Short overview.
- **[agent-rules.md](agent-rules.md)** — Modules, Git, security, POS/inventory expectations.
- **[setup.md](setup.md)** — Original greenfield checklist; **clone-based** onboarding is this document.

If setup or Cursor workflows change, update **this file** in the same PR.
