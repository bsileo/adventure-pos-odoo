# Shared sandbox environment (Google Cloud)

Notes for **humans and agents** working on the team’s shared Odoo sandbox on **GCP**. This is **not** local Docker; it complements [developer-onboarding.md](developer-onboarding.md).

**Do not** put passwords, API keys, or private SSH keys in this file. Operational identities below are for **project/account selection** only.

---

## GCP project and account (explicit selection)

Several GCP projects may be used on the same Windows machine. **Always** target this sandbox explicitly.

| Setting | Value |
|--------|--------|
| **Google account** | `adventopsapp@gmail.com` |
| **GCP project ID** | `adventure-pos-sandbox` |
| **GCP project number** | `48830482503` (used in tag bindings and some APIs) |
| **Resource tag** | `environment` = `Development` (`adventure-pos-sandbox/environment/Development`) |

When running `gcloud`, either use the **named configuration** below or pass `--account` and `--project` on every command.

---

## `gcloud` named configuration (recommended)

Create once (PowerShell or cmd):

```bash
gcloud config configurations create adventurepos-sandbox
gcloud config configurations activate adventurepos-sandbox
gcloud config set account adventopsapp@gmail.com
gcloud config set project adventure-pos-sandbox
```

Verify:

```bash
gcloud config list
```

Switch back to this sandbox later:

```bash
gcloud config configurations activate adventurepos-sandbox
```

List configurations:

```bash
gcloud config configurations list
```

---

## Explicit flags (when in doubt)

```bash
gcloud compute instances list --account=adventopsapp@gmail.com --project=adventure-pos-sandbox
```

Re-auth if needed:

```bash
gcloud auth login adventopsapp@gmail.com
```

For tools that use Application Default Credentials:

```bash
gcloud auth application-default login
```

(sign in as `adventopsapp@gmail.com` when the browser opens)

---

## SSH access model (Option B — instance / project metadata keys)

This sandbox uses **classic SSH keys** in **Compute Engine metadata** (not OS Login). GitHub Actions will use the same pattern: **private key** in a GitHub Actions secret; **public key** on the VM.

**Local key files (example paths — do not commit private key):**

| File | Purpose |
|------|--------|
| `%USERPROFILE%\.ssh\adventurepos_gcp_deploy` | **Private** — GitHub Actions secret + your local `ssh -i` if needed |
| `%USERPROFILE%\.ssh\adventurepos_gcp_deploy.pub` | **Public** — paste into VM creation metadata or `ssh-keys` file |

**Metadata format** (one line; `USERNAME` = Linux login on the VM, e.g. `deploy`):

```text
USERNAME:ssh-ed25519 AAAA... rest-of-public-key
```

Build a small file (e.g. `gcp-ssh-keys.txt`) with that single line, then pass it when creating the instance:

`--metadata-from-file ssh-keys=gcp-ssh-keys.txt`

**Conflict with OS Login:** If **project or instance** metadata has **`enable-oslogin`** = **`TRUE`**, **metadata `ssh-keys` are ignored**. For Option B, ensure OS Login is **off** at project default (delete the key) or set `enable-oslogin=FALSE` before relying on metadata keys. See [Set OS Login](https://cloud.google.com/compute/docs/instances/managing-instance-access#enable_os_login).

---

## `environment` tag reminder (terminal message from `gcloud`)

If you see:

`Project 'adventure-pos-sandbox' lacks an 'environment' tag...`

that is **separate from** `gcloud config`: your **active project can still be set correctly** (you should still see `Updated property [core/project]`). GCP is asking you to **label the project** for org governance using a resource tag whose **key** is `environment` and whose **value** is one of the allowed labels (e.g. `Production`, `Development`, `Test`, `Staging`).

For **`adventure-pos-sandbox`**, use **`Development`** or **`Staging`** — not `Production`.

**How to fix (org admin / someone with tag permissions):**

1. Follow Google’s guide: [Designate project environments with tags](https://cloud.google.com/resource-manager/docs/creating-managing-projects#designate_project_environments_with_tags).
2. Typical flow: ensure an **`environment` tag key** exists at the **organization** (or folder) level, create a **tag value** (e.g. `Development`), then **bind** that value to project **`adventure-pos-sandbox`** (Console **Tag Manager** / **gcloud resource-manager tags bindings create** as in the doc).

Until the binding exists, some orgs show this warning whenever you select the project; it does not block local `gcloud` use by itself.

---

## Handoff fields (fill in as setup progresses)

Agents and runbooks should use these once known:

| Field | Value / status |
|--------|----------------|
| `PROJECT_ID` | `adventure-pos-sandbox` |
| `PROJECT_NUMBER` | `48830482503` |
| `ZONE` | `us-central1-a` |
| `INSTANCE_NAME` | `adventurepos-sandbox-vm` |
| `EXTERNAL_IP` | **Ephemeral** — fetch current: `gcloud compute instances describe adventurepos-sandbox-vm --zone=us-central1-a --project=adventure-pos-sandbox --format="get(networkInterfaces[0].accessConfigs[0].natIP)"` |
| `DEPLOY_PATH` | `/srv/adventurepos/adventure-pos-odoo` (see **On the VM after SSH**) |
| `DEPLOY_BRANCH` | `develop` (expected integration branch for deploys) |
| Linux SSH user (Option B) | `deploy` (must match `ssh-keys` metadata line) |

---

## Windows / PowerShell notes

**`gcloud --metadata-from-file ssh-keys`:** `%USERPROFILE%` is **not** expanded by PowerShell. Use an explicit path, e.g.:

```powershell
--metadata-from-file "ssh-keys=$env:USERPROFILE\.ssh\gcp-ssh-keys.txt"
```

**First SSH connection:** When OpenSSH asks to confirm the host key, answer **`yes`**. If the prompt fails with `Host key verification failed` (non-interactive session), use:

```powershell
ssh -o StrictHostKeyChecking=accept-new -i "$env:USERPROFILE\.ssh\adventurepos_gcp_deploy" deploy@EXTERNAL_IP
```

Replace **`EXTERNAL_IP`** with the `natIP` from the `gcloud ... describe` command above (it **changes** if the VM is recreated unless you use a **static** IP).

**Boot disk size warning:** Ubuntu 22.04 on GCE usually **grows the root filesystem** on first boot; if `df -h` shows only ~10 GB, use Google’s [resize](https://cloud.google.com/compute/docs/disks/add-persistent-disk#resize_pd) guidance.

---

## On the VM after SSH (Docker + repo + Odoo)

Run these as the **`deploy`** user (use `sudo` where shown). **`DEPLOY_PATH`** below is `/srv/adventurepos/adventure-pos-odoo` — adjust if you clone elsewhere and update the handoff table.

### 1. Install Docker Engine + Compose plugin (Ubuntu 22.04)

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker deploy
```

Sign out and SSH back in so **`deploy`** is in group **`docker`**, then verify: `docker run --rm hello-world`

### 2. Clone the Git repo (private repo → GitHub deploy key)

1. In GitHub: repo **Settings → Deploy keys → Add deploy key** — paste a **new** `ssh-ed25519` **public** key generated **on the VM** (read-only). Do **not** reuse the GCE login key unless you intend to.
2. On the VM:

```bash
sudo mkdir -p /srv/adventurepos
sudo chown deploy:deploy /srv/adventurepos
cd /srv/adventurepos
ssh-keygen -t ed25519 -f ~/.ssh/github_adventurepos -N ""
cat ~/.ssh/github_adventurepos.pub
```

Add that `.pub` to GitHub, then:

```bash
cat >> ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_adventurepos
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
ssh -T git@github.com
git clone git@github.com:bsileo/adventure-pos-odoo.git
cd adventure-pos-odoo
git checkout develop
```

(Use your org’s URL if the remote differs.)

**If you see `Permission denied (publickey)`:** GitHub is not accepting the key the VM is offering. Check in order:

1. **Deploy key is on the same repository** you clone — **Settings → Deploy keys** for **`bsileo/adventure-pos-odoo`** (not only your user SSH keys, not another fork’s settings).
2. **Public key on GitHub matches the VM** — on the VM run `cat ~/.ssh/github_adventurepos.pub` and confirm the **entire** one-line key was pasted into **Add deploy key** (title e.g. `gcp-sandbox-deploy`). Re-add if unsure.
3. **Private key permissions** — `chmod 600 ~/.ssh/github_adventurepos`
4. **Verbose test** (see which key is tried):

   ```bash
   ssh -vT git@github.com 2>&1 | tail -30
   ```

   You want `Offering public key: ... github_adventurepos` then authentication success. If it offers a different key, fix **`~/.ssh/config`** (`IdentitiesOnly yes` and correct `IdentityFile`).
5. **Read access** — deploy key must **not** be created with “Allow write access” disabled is fine for `git clone`; ensure the key wasn’t deleted or disabled in GitHub.

**Temporary workaround:** clone with HTTPS and a [fine-grained or classic PAT](https://docs.github.com/en/authentication) (repo read) — less ideal than a deploy key; do not store the token in the repo.

### 3. Environment file

```bash
cp .env.example .env
nano .env   # set POSTGRES_PASSWORD to a strong value; optional OPENAI_API_KEY
```

### 4. GCP firewall for Odoo (port **8069**)

Default VPC allows **SSH**; it does **not** automatically allow **8069**. Create a rule (Console **VPC network → Firewall** or `gcloud`) allowing **tcp:8069** from **your IP** / team / `0.0.0.0/0` for a wide-open dev sandbox.

### 5. Start the stack (current repo compose)

From the repo root:

```bash
docker compose up -d
```

First-time DB init (if `/` returns 500): see [Makefile](Makefile) `init-db` — run the `docker compose exec odoo odoo ... -i base --stop-after-init` line with **`--db_password`** matching **`.env`**.

Then open `http://EXTERNAL_IP:8069`, install **Adventure Base** / **Adventure POS** per [developer-onboarding.md](developer-onboarding.md).

**Note:** Hardening (`docker-compose.server.yml`, internal-only Postgres, TLS) is a follow-up in-repo task; the steps above match today’s single [docker-compose.yml](docker-compose.yml).

---

## Related

- [agent-rules.md](agent-rules.md) — repo-wide agent behavior
- [architecture/tenant-provisioning.md](architecture/tenant-provisioning.md) — long-term hosting; **Odoo.sh** deferred for this sandbox phase
