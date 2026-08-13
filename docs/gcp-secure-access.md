# Secure Google Cloud developer access

Adventure POS development VMs use **OS Login + two-factor authentication + Identity-Aware Proxy (IAP)**. VMs must not expose SSH, RDP, Postgres, or Odoo directly to the internet.

## Google Cloud baseline

Project `adventure-pos-sandbox` is configured with:

- project metadata `enable-oslogin=TRUE`
- project metadata `enable-oslogin-2fa=TRUE`
- firewall rule `allow-ssh-ingress-from-iap`
  - source: `35.235.240.0/20`
  - target tag: `iap-ssh`
  - protocol: `tcp:22`
- legacy internet-wide SSH, RDP, and Odoo rules disabled

Every replacement VM must:

- have **no external IP** (`--no-address`)
- include the `iap-ssh` network tag
- set `block-project-ssh-keys=TRUE`
- use a dedicated least-privilege service account

## Developer IAM

Grant access to a Google Group when possible; use individual users only as a temporary bridge.

Required roles:

- `roles/iap.tunnelResourceAccessor`
- `roles/compute.osLogin` for shell access without `sudo`, or `roles/compute.osAdminLogin` only when `sudo` is required
- `roles/compute.viewer` so developers and tooling can resolve instance details

Developers who create/start/stop VMs need a separate, narrowly scoped lifecycle role. Do not use Owner or Editor for routine development.

All developer Google accounts must have Google 2-Step Verification enabled before connecting.

## Local workstation setup

Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), then run:

```bash
gcloud auth login
gcloud config configurations create adventurepos-sandbox
gcloud config configurations activate adventurepos-sandbox
gcloud config set project adventure-pos-sandbox
gcloud auth list
```

Create a private VM using the repo helper:

```powershell
.\scripts\remote-dev.ps1 create
.\scripts\remote-dev.ps1 start
.\scripts\remote-dev.ps1 bootstrap
```

```bash
bash ./scripts/remote-dev.sh create
bash ./scripts/remote-dev.sh start
bash ./scripts/remote-dev.sh bootstrap
```

SSH through IAP:

```powershell
.\scripts\remote-dev.ps1 ssh
```

```bash
bash ./scripts/remote-dev.sh ssh
```

No developer SSH key is pasted into VM or project metadata. `gcloud` and OS Login manage short-lived login credentials tied to the developer's Google identity.

## Access Odoo without opening port 8069

Keep this command running in a dedicated terminal:

```powershell
.\scripts\remote-dev.ps1 tunnel
```

```bash
bash ./scripts/remote-dev.sh tunnel
```

Then open <http://127.0.0.1:8069>. The browser connection travels through an authenticated IAP tunnel; port 8069 is not internet-accessible.

Use the same pattern for Postgres only when necessary:

```bash
gcloud compute start-iap-tunnel INSTANCE 5432 \
  --local-host-port=127.0.0.1:5432 \
  --zone=us-central1-a \
  --project=adventure-pos-sandbox
```

Do not create a public `tcp:5432` firewall rule.

## Cursor Remote SSH

Generate IAP-aware SSH configuration:

```powershell
.\scripts\remote-dev.ps1 cursor
```

```bash
bash ./scripts/remote-dev.sh cursor
```

Connect Cursor to the generated host named like:

```text
INSTANCE.us-central1-a.adventure-pos-sandbox
```

Open `/srv/adventurepos/adventure-pos-odoo`, not its parent directory.

## GitHub Actions deployment

The sandbox workflow uses GitHub OIDC and Google Workload Identity Federation; it must not store a VM private key or public IP.

Create a dedicated deploy service account and grant it only:

- `roles/iap.tunnelResourceAccessor`
- `roles/compute.osAdminLogin` on the sandbox VM/project as required
- `roles/compute.viewer`

Create a Workload Identity Pool/provider restricted to this repository and `develop` branch, then allow that principal to impersonate the deploy service account with `roles/iam.workloadIdentityUser`.

Configure repository secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER` = `projects/48830482503/locations/global/workloadIdentityPools/github-pool/providers/github-provider`
- `GCP_DEPLOY_SERVICE_ACCOUNT` = `adventurepos-sandbox-deploy@adventure-pos-sandbox.iam.gserviceaccount.com`

Configure repository variables if the defaults differ:

- `GCP_SANDBOX_INSTANCE` = `adventurepos-sandbox-vm`
- `GCP_SANDBOX_ZONE` = `us-central1-a`
- `GCP_SANDBOX_DEPLOY_PATH` = `/srv/adventurepos/adventure-pos-odoo`

The workflow SSHs as Linux user `deploy` through IAP (`gcloud compute ssh deploy@INSTANCE --tunnel-through-iap`).

Delete the obsolete secrets `GCP_SANDBOX_SSH_PRIVATE_KEY`, `GCP_SANDBOX_SSH_HOST`, and `GCP_SANDBOX_KNOWN_HOSTS` after the WIF workflow succeeds.

## Verification checklist

```bash
gcloud compute instances describe INSTANCE \
  --zone=us-central1-a \
  --project=adventure-pos-sandbox \
  --format='yaml(networkInterfaces,metadata.items,tags.items)'

gcloud compute firewall-rules describe allow-ssh-ingress-from-iap \
  --project=adventure-pos-sandbox

gcloud compute ssh INSTANCE \
  --zone=us-central1-a \
  --project=adventure-pos-sandbox \
  --tunnel-through-iap
```

Verify that the VM has no `accessConfigs` entry, has the `iap-ssh` tag, accepts OS Login with 2FA, and cannot be reached directly from the internet.
