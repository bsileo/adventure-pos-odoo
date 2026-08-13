# Cursor → GitHub → shared sandbox

> **Security baseline:** The sandbox now uses private VMs, OS Login, IAP, and Workload Identity Federation. Follow [gcp-secure-access.md](gcp-secure-access.md) instead of historical public-IP/static-key steps below.

Short path: edit in **Cursor**, land code on **`develop`**, and see it on the **GCP Odoo sandbox** (not your laptop Docker).

**Deeper reference:** [shared-environment.md](shared-environment.md) (GCP project, SSH, secrets, firewall). **Local-only Odoo:** [developer-onboarding.md](developer-onboarding.md). **Branches / PRs:** [development-tracking.md](development-tracking.md).

---

## 1. Start the sandbox VM (if it might be stopped)

From your **PC** (needs [`gcloud`](https://cloud.google.com/sdk/docs/install) and access to project **`adventure-pos-sandbox`** — see [shared-environment.md — gcloud configuration](shared-environment.md#gcloud-named-configuration-recommended)):

**Windows (PowerShell, repo root):**

```powershell
.\scripts\gcp-sandbox-vm.ps1 status   # RUNNING vs TERMINATED
.\scripts\gcp-sandbox-vm.ps1 start    # if stopped
```

**macOS / Linux / Git Bash:**

```bash
make gcp-vm-status
make gcp-vm-start   # if needed
```

The sandbox VM has **no public SSH/Odoo ports**. After start, wait a minute, then use IAP (`gcloud compute ssh ... --tunnel-through-iap` or the helpers in [gcp-secure-access.md](gcp-secure-access.md)). GitHub deploys do not depend on a public IP.

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

Pushing to **`develop`** runs **[`.github/workflows/deploy-gcp-sandbox.yml`](../.github/workflows/deploy-gcp-sandbox.yml)**: GitHub authenticates to GCP with Workload Identity Federation, SSHs through IAP as **`deploy`**, runs **`git reset --hard origin/develop`**, and **`docker compose up -d`**.

Check **GitHub → Actions → Deploy GCP sandbox** for the run. If it failed, confirm the VM is running and the WIF secrets in [gcp-secure-access.md](gcp-secure-access.md), then use **Run workflow** to retry.

---

## 4. See your change in Odoo

1. Open an IAP tunnel to Odoo (see [gcp-secure-access.md](gcp-secure-access.md)):

   ```powershell
   gcloud compute start-iap-tunnel adventurepos-sandbox-vm 8069 --local-host-port=127.0.0.1:8069 --zone=us-central1-a --project=adventure-pos-sandbox
   ```

2. Open **`http://127.0.0.1:8069`**.
3. **Python / XML / manifest** changes to addons often need **Apps → upgrade** the module (or `-u module` on the server); simple file sync alone is not always enough for Odoo to reload everything.
4. For a **working Tidewater dive shop** after a wipe (or first bootstrap), run the seed on the VM — see [seed-data.md](seed-data.md) / [shared-environment.md](shared-environment.md). Deploys alone do not reseed.

---

## 5. If the workflow did not deploy

- VM **running**? (`status` above.)
- WIF secrets **`GCP_WORKLOAD_IDENTITY_PROVIDER`** and **`GCP_DEPLOY_SERVICE_ACCOUNT`** still set?
- Run **Actions → Deploy GCP sandbox → Run workflow** manually on `develop`.

You can still SSH through IAP as `deploy` and run the same git/compose commands by hand (paths in [shared-environment.md](shared-environment.md)).

---

## 6. Reset the shared sandbox database (destructive)

Only when the team agrees: wipe Postgres, re-init **`base`**, and bootstrap **Tidewater** (see [shared-environment.md — Reset sandbox database](shared-environment.md#reset-sandbox-database-destructive)). **`make reset-db`** is for **local** Docker only. For a non-destructive Tidewater refresh, use **`gcp-sandbox-seed-tidewater.sh`**.
