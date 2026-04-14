# Cursor → GitHub → shared sandbox

Short path: edit in **Cursor**, land code on **`develop`**, and see it on the **GCP Odoo sandbox** (not your laptop Docker).

**Deeper reference:** [shared-environment.md](shared-environment.md) (GCP project, SSH, secrets, firewall). **Local-only Odoo:** [developer-onboarding.md](developer-onboarding.md). **Branches / PRs:** [development-tracking.md](development-tracking.md).

---

## 1. Start the sandbox VM (if it might be stopped)

From your **PC** (needs [`gcloud`](https://cloud.google.com/sdk/docs/install) and access to project **`adventure-pos-sandbox`** — see [shared-environment.md — gcloud configuration](shared-environment.md#gcloud-named-configuration-recommended)):

**Windows (PowerShell, repo root):**

```powershell
.\scripts\gcp-sandbox-vm.ps1 status   # RUNNING vs TERMINATED
.\scripts\gcp-sandbox-vm.ps1 start    # if stopped
.\scripts\gcp-sandbox-vm.ps1 ip       # current public IP
```

**macOS / Linux / Git Bash:**

```bash
make gcp-vm-status
make gcp-vm-start   # if needed
make gcp-vm-ip
```

After a **stop/start**, the **public IP can change**. Someone with repo admin access must update GitHub Actions secrets **`GCP_SANDBOX_SSH_HOST`** and usually **`GCP_SANDBOX_KNOWN_HOSTS`** (see [shared-environment.md — GitHub Actions](shared-environment.md#github-actions--auto-deploy-to-the-sandbox-develop)). Until that matches, deploys from GitHub will fail even if the VM is up.

Wait a minute after **`start`** before SSH or Odoo respond.

---

## 2. Work in Cursor

1. Open the **repo root** in Cursor (folder that contains `docker-compose.yml`).
2. Update **`develop`** and create a **feature branch** (do not commit straight to `develop`):

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feat/your-change
   ```

3. Edit code (e.g. under `addons/`). Commit with a clear message.
4. Push and open a **PR into `develop`**:

   ```bash
   git push -u origin feat/your-change
   ```

   Use GitHub’s **Compare & pull request** (or `gh pr create --base develop`).

5. Get the PR **reviewed and merged** to **`develop`**.

---

## 3. What happens on merge

Pushing to **`develop`** runs **[`.github/workflows/deploy-gcp-sandbox.yml`](../.github/workflows/deploy-gcp-sandbox.yml)**: it SSHs to the VM, **`git reset --hard origin/develop`** in the deploy directory, and **`docker compose up -d`**.

Check **GitHub → Actions → Deploy GCP sandbox** for the run. If it failed, fix secrets/host/IP per [shared-environment.md](shared-environment.md) or use **Run workflow** to retry after the VM and secrets are correct.

---

## 4. See your change in Odoo

1. Use the VM’s **public IP** (`gcp-sandbox-vm.ps1 ip` / `make gcp-vm-ip`).
2. Open **`http://<IP>:8069`** (firewall must allow **8069** — see [shared-environment.md](shared-environment.md#4-gcp-firewall-for-odoo-port-8069)).
3. **Python / XML / manifest** changes to addons often need **Apps → upgrade** the module (or `-u module` on the server); simple file sync alone is not always enough for Odoo to reload everything.

---

## 5. If the workflow did not deploy

- VM **running**? (`status` above.)
- **IP / known_hosts** secrets still valid after IP change?
- Run **Actions → Deploy GCP sandbox → Run workflow** manually on `develop`.

You can still **SSH** as `deploy` and run the same commands by hand on the VM if needed (paths in [shared-environment.md](shared-environment.md)).
