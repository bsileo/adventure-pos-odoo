# Smartwaiver ↔ Adventure POS — waiver sync

**Status:** Implemented for V1 (CRM ingest). Optional per-tenant module `adventure_smartwaiver`.

**Vendor:** [Smartwaiver](https://www.smartwaiver.com/) — REST API at `https://api.smartwaiver.com` ([API docs](https://api.smartwaiver.com/api/docs)).

## Business scenario

- Dive and adventure shops often collect **signed liability waivers** in Smartwaiver (kiosk, email link, or web).
- Staff need those waivers **inside Adventure POS / CRM** next to the customer (`res.partner`), without making every tenant pay for or run the integration.
- Guests sometimes **sign before** a customer record exists (or with a different email). Those waivers must still be stored and linked later.

**Primary sync direction:** Smartwaiver → Odoo (scheduled poll and webhook queue drain). Creating or sending waivers from Odoo is out of V1.

## Enablement (optional / billable)

1. Install **Adventure Smartwaiver** (`adventure_smartwaiver`) on that shop’s tenant database only.
2. Configure the Smartwaiver API key under **Settings → Adventure Smartwaiver** (or set env `SMARTWAIVER_API_KEY`).
3. Cron jobs poll signed waivers and drain the Smartwaiver webhook queue.
4. Tenants that do not use Smartwaiver leave the module uninstalled.

This matches the repository pattern: optional features are **install-per-tenant apps**, not hard-wired into `adventure_pos`.

## V1 scope (confirmed)

| In V1 | Out of V1 (later) |
|-------|-------------------|
| Pull / upsert signed waivers by `waiverId` | POS checkout warn/block rules |
| Match to `res.partner` by email (then name) | Auto-create partners from waivers |
| Store **unmatched** / **ambiguous** waivers | Dynamic waiver create / prefill / SMS |
| Manual link / unlink | FareHarbor participant cross-link |
| Re-match when a partner gains a matching email | Template-based “required waiver” product rules |
| Partner smart button + waiver menus | Check-ins / group reservations |
| Webhook queue drain + on-demand PDF | Pushing Odoo customers into Smartwaiver |

## Partner matching policy

Aligned with the CRM-first approach in [FareHarbor POS sync](fareharbor-pos-sync.md), with one important difference: **Smartwaiver never auto-creates `res.partner` in V1.**

1. Normalize email (lowercase, trim).
2. If the waiver has an email → find partners with that email. **Exactly one** → `matched` / method `email`. **More than one** → `ambiguous` (no auto-link). **None** → keep `unmatched`.
3. Else try normalized first + last name. **Exactly one** high-confidence hit → `matched` / method `name`; otherwise `unmatched` or `ambiguous`.
4. Staff may **manually link** a waiver to a partner (`match_state=manual`).
5. When a partner is created or its email changes, unmatched/ambiguous waivers with that email are **re-matched**.

## Odoo modeling

| Concept | Purpose |
|--------|---------|
| `smartwaiver.waiver` | One row per Smartwaiver `waiverId` (idempotent upsert) |
| `partner_id` | Optional link to `res.partner` |
| `match_state` | `matched` / `unmatched` / `manual` / `ambiguous` |
| `match_method` | `email` / `name` / `manual` / `none` |
| JSON fields | Participants and custom waiver fields (promote to columns later if needed) |
| `pdf_attachment_id` | Optional PDF fetched on demand |
| `res.partner` inherit | Smart button, waiver count, computed status, search action |
| Settings | API key, sync enable, template allowlist, PDF preference |

## Smartwaiver API surfaces used

Auth: `Authorization: Bearer <API_KEY>`. Account limit **100 requests/min**; search is separately limited to **5/min**.

| Endpoint | Role |
|----------|------|
| `GET /v4/waivers` | Incremental poll / backfill |
| `GET /v4/waivers/{id}` | Full detail; optional `pdf=true` |
| `GET /v4/search` + `/v4/search/{guid}/results` | On-demand search by email / name for a partner |
| `GET /v4/templates` | Optional template allowlist in settings |
| Webhook config + **webhook queues** | Near-real-time ingest via queue drain cron |

## Sync surfaces

| Mechanism | Role |
|-----------|------|
| `ir.cron` poll | List recent waivers, upsert, respect rate limits |
| `ir.cron` webhook queue | Drain Smartwaiver account webhook queue |
| Settings “Sync now” | Manual poll |
| Partner “Search Smartwaiver” | Search API by partner email/name, upsert hits |
| Partner write (email) | Trigger re-match of unmatched waivers |

## Security and secrets

- Do **not** commit API keys. Prefer Settings → system parameters, or environment variable `SMARTWAIVER_API_KEY`.
- Staff group can read/link waivers; configuration of the API key is limited to Settings / system administrators.

## Module layout

```
addons/adventure_smartwaiver/
```

Depends on `adventure_base` and `contacts` only (no hard dependency on `adventure_pos`).

## Related docs

- [FareHarbor POS sync](fareharbor-pos-sync.md) — partner resolution and optional-integration pattern
- [Core model](../data-model/core-model.md) — tenant-local `res.partner`
- [Agent rules](../agent-rules.md) — module-first design and documentation workflow
- Published site: [Event Ops Developer Docs](https://bsileo.github.io/adventure-pos-odoo/)
