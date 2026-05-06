# Remote development on GCP

Use this workflow when you want **Cursor on your laptop** but want **Odoo, Postgres, and Docker** to run on a **developer-owned GCP VM** instead of your machine.

This is a **developer convenience** workflow for lowering local CPU/RAM usage. It is **separate from** the shared sandbox documented in [shared-environment.md](shared-environment.md).

## Recommended developer experience

1. Start your VM from the repo.
2. Connect Cursor to the VM with **Remote SSH**.
3. Open the repo on the VM.
4. Run Docker Compose from Cursor's remote terminal.
5. Work normally in Cursor while the heavy runtime stays on GCP.
6. Stop the VM when you are done for the day.

## Prerequisites

On your laptop:

- **Cursor**
- **`gcloud` CLI** authenticated to project `adventure-pos-sandbox`
- **OpenSSH client**
- access to your developer VM in GCP

On the VM:

- Ubuntu/Linux shell access
- a user such as `deploy`
- GitHub access to clone the repo

## Naming and defaults

The helper scripts assume this default instance naming pattern:

- instance name: `adventurepos-dev-<your-username>`
- project: `adventure-pos-sandbox`
- zone: `us-central1-a`
- VM user: `deploy`
- repo path: `/srv/adventurepos/adventure-pos-odoo`

Override any of these with shell environment variables before running the scripts:

- `REMOTE_DEV_GCP_PROJECT`
- `REMOTE_DEV_GCP_ZONE`
- `REMOTE_DEV_GCP_INSTANCE`
- `REMOTE_DEV_INSTANCE_PREFIX`
- `REMOTE_DEV_VM_USER`
- `REMOTE_DEV_REPO_PATH`
- `REMOTE_DEV_REPO_URL`
- `REMOTE_DEV_REPO_BRANCH`
- `REMOTE_DEV_ODOO_PORT`
- `REMOTE_DEV_SSH_KEY`
- `REMOTE_DEV_SERVICE_ACCOUNT`
- `REMOTE_DEV_ACCESS_SCOPES`

## First-time VM bootstrap

From your laptop:

### GCP login

```powershell
gcloud auth login
gcloud config set project adventure-pos-sandbox
```

The project admin must grant your Google account the custom remote-dev role and `roles/iam.serviceAccountUser` on:

```text
adventurepos-remote-dev-vm@adventure-pos-sandbox.iam.gserviceaccount.com
```

### PowerShell

```powershell
.\scripts\remote-dev.ps1 init-ssh
.\scripts\remote-dev.ps1 create
.\scripts\remote-dev.ps1 start
.\scripts\remote-dev.ps1 bootstrap
```

### Bash / Git Bash / macOS / Linux

```bash
bash ./scripts/remote-dev.sh init-ssh
bash ./scripts/remote-dev.sh create
bash ./scripts/remote-dev.sh start
bash ./scripts/remote-dev.sh bootstrap
```

If you already have a VM, skip `create` and set `REMOTE_DEV_GCP_INSTANCE` to that instance name before running the other commands.

If your laptop does not already have an SSH key pair, run `init-ssh` first. That creates `~/.ssh/id_ed25519` and `~/.ssh/id_ed25519.pub`, which `create` uses by default for VM access.

The bootstrap script:

- installs Docker and the Compose plugin if missing
- installs Git if missing
- creates a dedicated GitHub SSH key on the VM
- trusts the `github.com` host key on the VM
- ensures the repo exists at the remote path
- creates `.env` from `.env.example` if needed

If GitHub access is not ready yet, bootstrap prints the VM public key and you can add it in GitHub at:

- **Repo → Settings → Deploy keys → Add deploy key** — enable **Allow write access** so you can `git push` and use Cursor’s remote Git/PR workflow from the VM. The key is still limited to this repository.
- **GitHub user settings → SSH and GPG keys** — only if you prefer account-level SSH access instead of a deploy key (broader access across repos that user can reach).

The `create` step uses these defaults unless you override them with environment variables:

- machine type: `e2-standard-2`
- boot disk: `50GB`
- image family: `ubuntu-2204-lts`
- image project: `ubuntu-os-cloud`
- login user on the VM: `deploy`
- VM service account: `adventurepos-remote-dev-vm@adventure-pos-sandbox.iam.gserviceaccount.com`
- access scopes: `cloud-platform`
- firewall rule: `adventurepos-remote-dev-odoo`
- Odoo source ranges: `0.0.0.0/0`

`create` uses your local public SSH key from `~/.ssh/id_ed25519.pub` by default, or `~/.ssh/id_rsa.pub` if needed. Override with `REMOTE_DEV_SSH_PUBLIC_KEY_PATH`.

`create` also attaches the low-privilege remote-dev VM service account by default. Override it with `REMOTE_DEV_SERVICE_ACCOUNT` only if the project admin gives you a different service account.

`create` also ensures a GCP firewall rule exists for browser access to Odoo on port `8069`. Override the rule name with `REMOTE_DEV_FIREWALL_RULE`, or narrow browser access with `REMOTE_DEV_ODOO_SOURCE_RANGES` such as `203.0.113.10/32`.

After bootstrap, SSH back in once if Docker was just installed so the `docker` group takes effect.

If bootstrap cannot clone the repo yet, it will print the VM's GitHub public key. Add that key to GitHub as a **deploy key with Allow write access** (recommended) or as an SSH key on your user account, then rerun `bootstrap`.

## Daily workflow

### 1. Start the VM

```powershell
.\scripts\remote-dev.ps1 start
```

or:

```bash
bash ./scripts/remote-dev.sh start
```

### 2. Get Cursor connection details

```powershell
.\scripts\remote-dev.ps1 cursor
```

or:

```bash
bash ./scripts/remote-dev.sh cursor
```

That prints the current host, IP, VM user, repo path, and a suggested SSH config snippet you can paste into your SSH config for Cursor Remote SSH.

### 3. Connect Cursor with Remote SSH

In Cursor:

1. Open **Remote SSH**
2. Connect to the host printed by the script
3. Open `/srv/adventurepos/adventure-pos-odoo` or your configured repo path

Open the **repo folder itself**, not its parent. For the default setup, that means:

- Correct: `/srv/adventurepos/adventure-pos-odoo`
- Incorrect: `/srv/adventurepos`

If you open the parent folder, Cursor may connect successfully but Source Control and agents may not detect the Git repository because `.git/` is inside the child folder.

Once connected, the workspace is running on the VM. Search, terminal commands, git, AI context, and Docker commands all operate against the remote machine.

### Source Control Is Empty

If Cursor connects but the Source Control sidebar is empty, check the opened folder first. In the remote terminal:

```bash
git rev-parse --show-toplevel
```

It should print:

```text
/srv/adventurepos/adventure-pos-odoo
```

If it says `not a git repository`, reopen the folder `/srv/adventurepos/adventure-pos-odoo` from Cursor's remote window.

### 4. Start the app stack on the VM

From Cursor's **remote terminal**:

```bash
docker compose up -d
```

Or from your laptop with the helper script:

```powershell
.\scripts\remote-dev.ps1 up
```

```bash
bash ./scripts/remote-dev.sh up
```

The helper now runs Odoo DB initialization automatically on first boot if the core tables are missing.

### 5. Initialize a brand-new database once

Usually this is no longer manual because `remote-dev up` auto-initializes the DB on first boot. If you need to rerun the check manually:

```powershell
.\scripts\remote-dev.ps1 init-db
```

or:

```bash
bash ./scripts/remote-dev.sh init-db
```

If you are already SSH'd into the VM and standing in the repo:

```bash
bash ./scripts/odoo-init-db.sh
```

That script installs **`base`** with **`--without-demo=all`** (no Odoo demonstration/sample data), same as **`make init-db`** locally.

The shared helper script falls back between `POSTGRES_*` and Odoo's existing `USER` / `PASSWORD` env vars so it works against both the updated branch and older remote checkouts.

### 6. Open Odoo

```powershell
.\scripts\remote-dev.ps1 open
```

or:

```bash
bash ./scripts/remote-dev.sh open
```

### 7. Stop the VM when done

```powershell
.\scripts\remote-dev.ps1 stop
```

or:

```bash
bash ./scripts/remote-dev.sh stop
```

## Pushing work from the VM

**Recommended:** Register the VM’s SSH public key as a repo **deploy key** with **Allow write access** checked. You can still clone and pull; you can also `git push` from the VM and use Cursor’s remote source control / branch sync without copying commits through your laptop first. The credential remains scoped to **this repository** only.

Use **[branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)** on branches such as `develop` and `main` so pushes from the VM (or anywhere) follow the same review and merge rules you want for the team.

### Typical flow (write-enabled deploy key)

1. On the VM, commit your work:

   ```bash
   cd /srv/adventurepos/adventure-pos-odoo
   git status
   git add .
   git commit -m "your message"
   ```

2. Push your branch and open a PR as you would locally, for example:

   ```bash
   git push -u origin your-feature-branch
   ```

3. Open the PR on GitHub (web UI, `gh pr create`, or Cursor’s GitHub integration if signed in).

After the PR is merged, sync both laptop and VM checkouts to `develop` as usual (`git checkout develop`, `git pull`, delete the merged feature branch).

### Optional: read-only deploy key + push from laptop

If the deploy key does **not** have write access, `git push` from the VM fails with:

```text
ERROR: The key you are authenticating with has been marked as read only.
```

That is stricter for security (a compromised VM cannot push) at the cost of workflow friction. In that case, keep commits on the VM, then on your **laptop** use `fetch-branch` to pull the branch over SSH from the VM and push to `origin`:

```powershell
.\scripts\remote-dev.ps1 fetch-branch feature/your-branch
```

Or from Bash:

```bash
bash ./scripts/remote-dev.sh fetch-branch feature/your-branch
```

The helper creates or updates a local `gcp-dev` remote pointing at the VM, fetches the branch, checks it out locally, and pushes to `origin`.

If you need the same flow manually (replace host, user, path, and branch):

```powershell
git remote add gcp-dev deploy@adventurepos-dev-yourname:/srv/adventurepos/adventure-pos-odoo
git fetch gcp-dev feature/your-branch
git checkout -b feature/your-branch FETCH_HEAD
git push -u origin feature/your-branch
```

If `gcp-dev` already exists, skip `git remote add`.

After the PR is merged, sync both environments to `develop` and delete the merged feature branch on each machine you use.

## Security and data notes

- Postgres now binds to `127.0.0.1` by default, which is safer for remote VMs.
- If you need database access from your laptop, use **SSH tunneling** instead of exposing `5432` publicly.
- Odoo remains reachable on port `8069`. The helper defaults to `0.0.0.0/0` for first-time ease, so set `REMOTE_DEV_ODOO_SOURCE_RANGES` if you want to restrict it to your IP or office range.
- The VM is intended to be **persistent** so your Postgres data and checked-out repo survive stop/start cycles.

## Why this fits Odoo + Postgres

- Odoo day-to-day work is mostly **source changes** in `addons/`, not image publishing.
- Postgres benefits from a **persistent VM disk and Docker volume** instead of disposable rebuilds.
- Cursor **Remote SSH** avoids a fragile file-sync loop because the repo, Docker Compose, Odoo, and Postgres all live on the same VM.


## Related files

- [developer-onboarding.md](developer-onboarding.md) for the normal local Docker path
- [shared-environment.md](shared-environment.md) for the shared sandbox
- [../scripts/remote-dev.ps1](../scripts/remote-dev.ps1) for Windows lifecycle helpers
- [../scripts/remote-dev.sh](../scripts/remote-dev.sh) for Bash lifecycle helpers
- [../scripts/remote-dev-bootstrap.sh](../scripts/remote-dev-bootstrap.sh) for one-time remote VM bootstrap
