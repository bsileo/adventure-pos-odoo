# Extra addons (`addons/`)

This directory is bind-mounted to **`/mnt/extra-addons`** in the Odoo container ([`docker-compose.yml`](../docker-compose.yml)). Odoo loads **one module per immediate subdirectory** that contains `__manifest__.py` — do not nest modules under another folder unless you add that folder as a separate addons root.

## Stack version (verify before buying App Store assets)

| Source | Value |
|--------|--------|
| Image | [`Dockerfile`](../Dockerfile): `FROM odoo:19.0` |
| Compose tag | [`docker-compose.yml`](../docker-compose.yml): `adventure-pos-odoo:19.0` |

**Rule:** App Store modules and themes must match your Odoo **major** version (here **19.0**). For example, a listing under `…/themes/20.0/…` targets Odoo **20** and is not supported on this stack until the project upgrades Odoo.

## Adding a third-party theme or module (e.g. App Store ZIP)

1. Obtain the package from the vendor (purchase/download per their license).
2. Extract the archive so you have a **single directory** whose root contains `__manifest__.py` and `__init__.py`.
3. Place that directory **directly under** `addons/` (e.g. `addons/my_backend_theme/`). The folder name must be a valid Python package identifier.
4. Restart Odoo: `docker compose restart odoo`.
5. In the UI: **Apps** → **Update Apps List** → search for the module → **Install** (or **Upgrade** after code updates).

Confirm your license allows committing vendor code to your git repo and deploying from CI if you track it in source control.

## Updates

When the vendor publishes a new ZIP, replace the module directory (or merge changes), bump/review `__manifest__.py` version if needed, restart Odoo, and **Upgrade** the module from **Apps**.
