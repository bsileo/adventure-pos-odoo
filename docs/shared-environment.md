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

## Handoff fields (fill in as setup progresses)

Agents and runbooks should use these once known:

| Field | Value / status |
|--------|----------------|
| `PROJECT_ID` | `adventure-pos-sandbox` |
| `PROJECT_NUMBER` | `48830482503` |
| `ZONE` | _(e.g. `us-central1-a`) — add when VM exists_ |
| `INSTANCE_NAME` | _(add when VM exists)_ |
| `DEPLOY_PATH` | _(absolute path to repo clone on VM)_ |
| `DEPLOY_BRANCH` | `develop` (expected integration branch for deploys) |

---

## Related

- [agent-rules.md](agent-rules.md) — repo-wide agent behavior
- [architecture/tenant-provisioning.md](architecture/tenant-provisioning.md) — long-term hosting; **Odoo.sh** deferred for this sandbox phase
