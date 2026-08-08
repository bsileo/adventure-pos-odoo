# Client Web Portal Architecture

!!! warning "Architecture agreed — implementation in progress"

    Planning decisions are closed in [Decisions confirmed](#decisions-confirmed-review). **Build is underway:** `adventure_website` and `adventure_equipment_portal` ship in this workstream. Treat incomplete portal behavior as WIP until modules are installed/upgraded on target databases.

**Audience:** Product, operations, and developers planning customer self-service for adventure shops (dive, ski, etc.) on the Adventure POS Odoo stack.

**Related today:**

- Equipment lifecycle design — draft PR [#73](https://github.com/bsileo/adventure-pos-odoo/pull/73) (canonical doc path once merged: `docs/architecture/equipment-management.md`); proposes `adventure_equipment_portal` as Phase 4
- Equipment registry implementation — draft PR [#74](https://github.com/bsileo/adventure-pos-odoo/pull/74) (`adventure_equipment`); service/scuba packs [#79](https://github.com/bsileo/adventure-pos-odoo/pull/79) / [#80](https://github.com/bsileo/adventure-pos-odoo/pull/80)
- [AdventurePOS vertical module architecture](adventurepos-vertical-module-architecture.md) — platform vs vertical packs; Community / Odoo-native UI bias
- [Tidewater demo seed](tidewater-demo-seed.md) — module-owned demo contributors for sandbox demos
- [Core data model](../data-model/core-model.md) — one operational tenant DB per shop; ecommerce/website visibility is tenant-local
- [Tenant provisioning](tenant-provisioning.md) — per-tenant module install and baseline config
- [Scuba training and scheduling (future)](scuba-training-scheduling.md) — later customer portal session selection
- Third-party themes: [`addons/README.md`](../../addons/README.md) (Odoo **19.0** App Store themes under `addons/`)

**Out of scope for this plan:** website **content migration** from legacy shop sites into Odoo (handled by a separate migration project). This plan assumes greenfield or parallel Odoo Website setup, not cutover of existing marketing pages.

**Published docs:** when this page is merged, it will appear on [Event Ops Developer Docs](https://bsileo.github.io/adventure-pos-odoo/).

---

## Decisions confirmed (review)

| # | Decision | Status |
|---|----------|--------|
| 1 | **Hosting pattern = A (Odoo-hosted full site).** AdventurePOS will provide full client websites on Odoo Website; the customer portal is part of that site, not a separate hybrid/portal-only product. Tidewater demos use the same pattern. | **Confirmed** |
| 2 | **This workstream keeps the public website minimal.** A simple Tidewater homepage with **Sign in / login** and a link into the **equipment portal** is enough for MVP. Rich marketing pages, multi-page IA, and content migration remain out of scope here. | **Confirmed** |
| 3 | **Tidewater demo customer journey (MVP).** Homepage → login → list gear → asset detail → register external item → staff verify. **Not** mandatory for this demo: orders history, profile edit, or a documents-only flow. | **Confirmed** |
| 4 | **Portal signup = open self-registration.** Any email may create a portal user via standard Odoo `auth_signup` (not invite-only). Pair with normal portal ↔ partner linking / matching so equipment ownership still attaches to the right contact. | **Confirmed** |
| 5 | **Customer profile editing (address/phone/etc.) is out of this workstream.** Deferred to a **separate later workstream**; MVP portal does not include profile self-service outside equipment flows. | **Confirmed** |
| 6 | **Tidewater theme = default Odoo Website + company logo/colors.** No App Store theme or first-party `theme_tidewater` required for MVP; richer theming can follow later. | **Confirmed** |
| 7 | **Create thin `adventure_website` in P1** for pattern A minimal homepage, config-as-code, and Tidewater seed hooks (do not stuff homepage-only XML into `dive_shop_pos` / equipment portal). | **Confirmed** |
| 8 | **Sandbox URLs are path-based** on the existing sandbox host (homepage + `/web/login` + `/my/...`). Custom domain / DNS not required for Tidewater MVP demos. | **Confirmed** |
| 9 | **Household sharing = single `partner_id` owner** for portal MVP (match equipment Phase 1 contact-only ownership). No commercial-child / family share in this release. | **Confirmed** |
| 10 | **Customer-editable equipment fields:** nickname, notes, customer-visible photos/docs. **Read-only for customers:** serial/identifiers, category, verification state, lifecycle/shop fields. Service completions remain staff-only. | **Confirmed** |
| 11 | **Portal MVP is registry-only** for service: do **not** require service due/history UI until service modules are stable and explicitly pulled into a later slice. | **Confirmed** |
| 12 | **Document uploads:** use standard Odoo attachment/filestore behavior for MVP; enforce portal document visibility whitelist. Tighten size/count/type quotas later if needed. | **Confirmed** |
| 13 | **“Purchased at the shop” in Tidewater demo = staff-seeded / manually linked verified assets.** Sale/POS auto-create (equipment Phase 3) is **not** required to call the portal demo done. | **Confirmed** |
| 14 | **Sandbox demo credentials:** seed **fixed fictional portal passwords** and document them in [seed-data.md](../seed-data.md) (not invite-token-only). | **Confirmed** |
| 15 | **Outbound email on sandbox:** bypass acceptable for MVP demos (seeded passwords / documented test path). Production tenants use normal Odoo mail for signup/reset. | **Confirmed** |
| 16 | **Portal/equipment record rules are company-aware from day one**, even though Tidewater is single-company. | **Confirmed** |
| 17 | **Build sequencing:** `adventure_equipment_portal` waits until `adventure_equipment` is on `develop`. **`adventure_website` (minimal homepage) may proceed in parallel** before that merge. | **Confirmed** |
| 18 | **No dependency on the website content migration project** for portal MVP. | **Confirmed** |

All planning questions for this workstream are closed via explicit product answers or the adopted recommended defaults below.

---

## Purpose

Define how AdventurePOS will give each shop a **branded customer portal** that:

1. Reuses **off-the-shelf Odoo Website + Portal** (Community) as far as practical.
2. Lives on the shop’s **Odoo-hosted website** (pattern A), with theme and branding so portal and public pages share one presence—expandable to fuller retail sites over time.
3. Exposes domain features—starting with **customer equipment**—through installable Adventure modules rather than a separate SPA or custom CMS.
4. Can be demonstrated on the **Tidewater Dive Shop** sandbox with a minimal public homepage, sample portal customers, and gear.

---

## Current repository findings

| Area | Finding |
|------|---------|
| **Odoo version / edition** | **19.0** Community image (`Dockerfile` / compose). Enterprise Website themes / eCommerce extras are **not** assumed; design Community-first with optional Enterprise bridges later. |
| **Custom website/portal modules** | **None** under `addons/` on `develop`. No `website_*` / `*_portal` Adventure modules yet. |
| **Equipment domain** | Designed in draft equipment architecture ([PR #73](https://github.com/bsileo/adventure-pos-odoo/pull/73)); Phase 1 staff registry and later service/scuba packs exist as **in-flight draft PRs**. Portal is explicitly **deferred** to `adventure_equipment_portal`. |
| **Rental / training** | Shop rental fleet is a **sibling** domain (`adventure.rental.asset`). Training design mentions portal session selection as a **later** phase—do not block portal MVP on training. |
| **Tenant model** | **One PostgreSQL DB per shop.** Website, theme, portal users, and equipment data are all **tenant-local**. |
| **Themes today** | Documented path: install Odoo **19.0** App Store theme modules under `addons/` ([`addons/README.md`](../../addons/README.md)). No first-party Adventure “shop theme” module yet. |
| **Tidewater seed** | Seeds company, rental products/assets, and story customers (e.g. certified / uncertified divers). **No** portal users, website pages, or customer-owned equipment assets in the orchestrator yet. |
| **Migrations** | D360 and related runbooks are separate; **website content migration is out of scope** here. |

---

## Product framing

### What “client web portal” means here

For each tenant shop:

| Layer | Role | Odoo building blocks (preferred) |
|-------|------|----------------------------------|
| **Public website shell** | Brand, navigation, marketing pages the shop chooses to host in Odoo | `website`, theme module(s), Website Builder / pages, company logo & colors |
| **Authenticated portal** | Logged-in customer self-service | `portal`, `auth_signup` (open self-registration), `portal` home + custom portal menus |
| **Domain features** | Equipment (first), later orders, documents, training, service booking, etc. | Thin `adventure_*_portal` modules: Controllers + QWeb + record rules |
| **Staff backend** | Authoritative ops (verify gear, complete service, manage customers) | Existing backend apps (`adventure_equipment`, etc.) — unchanged source of truth |

The portal is **not** a second application with its own database or React/Tailwind frontend. That matches the vertical architecture rule: prefer Odoo OWL/QWeb and avoid independent frontend apps for Adventure surfaces ([vertical module architecture](adventurepos-vertical-module-architecture.md)).

### Relationship to the wider retail / online presence

**Confirmed product direction: pattern A — Odoo-hosted full site.** Future clients get websites on Odoo; Tidewater demonstrates that path. Hybrid (B) and portal-only (C) are not the target architecture for AdventurePOS-delivered sites. Feature portal modules should still avoid hard-coding assumptions that *many* marketing pages exist, so a **minimal homepage MVP** and a later richer site both work without rewriting equipment portal code.

| Pattern | Description | Status for AdventurePOS |
|---------|-------------|-------------------------|
| **A. Odoo-hosted site** | Marketing + shop + portal all on Odoo Website | **Chosen.** Theme + menus integrate portal under “My Account” / “My Equipment”. MVP public surface may be a single homepage. |
| **B. Hybrid** | Marketing on external CMS; Odoo hosts portal on a subdomain | Not the product default; do not optimize Tidewater or platform shell for this |
| **C. Minimal portal-only** | Little/no public marketing; invite links into `/my` only | Not the product default; insufficient for “we provide full websites” |

### MVP public website scope (this workstream)

Keep the Odoo Website **thin** while still being pattern A:

- One **homepage** (Tidewater-branded chrome: logo, shop name, short blurb).
- Clear **Sign in / Log in** entry to the portal.
- A visible path to **My Equipment** (menu and/or homepage CTA) once the customer is authenticated (and a login prompt when not).
- No requirement in this stream for multi-page marketing IA, blog, class catalogs, or migrated legacy content.

**Website content migration** (importing existing pages/media from legacy sites) remains **out of scope** for this workstream.

---

## Architectural principles

1. **Odoo-native first** — Prefer `website`, `portal`, `auth_signup`, `mail`, `ir.attachment`, Website themes, and Controllers/QWeb over custom SPAs.
2. **Feature modules, not a mega-portal** — Shell/branding configuration stays thin; each domain ships `adventure_<domain>_portal` (or portal controllers inside an optional portal extra) that can be installed per tenant.
3. **Same tenant DB** — Portal users are `res.users` with portal group linked to `res.partner`; record rules enforce **own partner only** (single `partner_id` owner for MVP; no household share yet).
4. **Staff remains authoritative** — Customer-created or edited records use verification / limited fields (already sketched for equipment).
5. **Theme-compatible UI** — Portal templates use Bootstrap / Odoo Website semantic classes and SCSS variables so App Store or custom themes re-skin them without forking controllers.
6. **Community-first** — No hard dependency on Enterprise eCommerce, Appointment, or proprietary themes for MVP.
7. **Demo-ready** — Any portal-capable module includes a **Tidewater contributor** (portal users + sample domain rows) per [tidewater-demo-seed.md](tidewater-demo-seed.md).
8. **Configuration as code** for agreed sandbox defaults (website name, portal menus, auth settings) — not only UI clicks on one database ([agent-rules](../agent-rules.md)).

---

## Proposed module shape

### Platform / shell (new)

| Module (proposed) | Responsibility | Depends on |
|-------------------|----------------|------------|
| **`adventure_website`** (thin shell) | Tenant website baseline for pattern A: enable Website/Portal, company → website defaults, **minimal homepage** (login + equipment portal entry), shared SCSS/portal chrome helpers, documented theme install hooks | `website`, `portal`, `adventure_base` |
| **Theme choice** | **MVP:** default Odoo Website + Tidewater/`res.company` logo and colors. App Store or first-party themes are optional later polish—not required to start. | `website` |

`adventure_website` should stay **domain-agnostic**. It must not own equipment models.

### Domain portal modules (pattern)

| Module | Responsibility | Status vs equipment roadmap |
|--------|----------------|------------------------------|
| **`adventure_equipment_portal`** | Customer list/detail of owned assets; register external gear; limited edits; portal-safe documents; portal record rules + HttpCase tests | Equipment Phase 4 (equipment architecture draft / PR #73) |
| Future: training / rental / orders portal extras | Same pattern: Controllers + QWeb + ACL | Later |

### Dependency sketch

```mermaid
flowchart TD
  website["website + portal"]
  theme["theme_* App Store or thin demo theme"]
  advweb["adventure_website thin shell"]
  equip["adventure_equipment"]
  eqportal["adventure_equipment_portal"]
  svc["adventure_equipment_service optional"]
  scuba["adventure_equipment_scuba optional"]
  dive["dive_shop_pos / Tidewater orchestrator"]

  website --> theme
  website --> advweb
  website --> eqportal
  equip --> eqportal
  equip --> svc
  svc --> scuba
  advweb -.-> dive
  eqportal -.-> dive
  scuba -.-> dive
```

Install sets (examples):

- **Staff only:** `adventure_equipment` (+ service/scuba) — no website required.
- **Portal + website (pattern A, MVP):** `website` + `portal` + thin theme/branding + `adventure_website` (minimal homepage) + `adventure_equipment` + `adventure_equipment_portal` (+ scuba for dive demos) + Tidewater seed contributors.
- **Later richer site:** same stack; add Website pages/menus/theme polish without changing equipment portal modules.

---

## Branding and theming strategy

### Recommended approach

1. **MVP:** Default Odoo Website theme plus Tidewater / `res.company` **logo and colors** (no App Store theme required to start).
2. **Adventure portal templates:** Use semantic classes (`o_portal_*`, Bootstrap utilities, theme CSS variables). Avoid hard-coded brand colors in Python/XML for equipment (or other) portal pages.
3. **Later optional:** App Store theme or thin first-party demo theme only if default chrome is insufficient for sales demos.
4. **Do not** build a parallel “Adventure theme system,” React design system, or Tailwind layer for the portal.

### Merge with wider online presence

| Concern | Approach |
|---------|----------|
| **Visual continuity** | Same logo, primary/secondary colors via company branding (+ optional later theme) |
| **Navigation** | Minimal menus: Home, Sign in / My Account, My Equipment (when authenticated) |
| **Domains** | Tidewater MVP: path-based on sandbox URL; custom domains documented later for production tenants |
| **SSO / social login** | Deferred; MVP = email/password portal users |
| **eCommerce** | Out of MVP; `website_sale` may be added later without redesigning equipment portal modules |

---

## Equipment portal (first domain feature)

Align with the equipment lifecycle architecture (draft PR [#73](https://github.com/bsileo/adventure-pos-odoo/pull/73); canonical path `docs/architecture/equipment-management.md` once merged) rather than inventing a second equipment model.

### Customer capabilities (MVP target)

| Capability | Notes |
|------------|-------|
| Sign in / sign up / reset password | Open `auth_signup` + mail (sandbox may bypass mail via seeded passwords) |
| See “My Equipment” list | Assets where `partner_id` is the portal user’s partner (**single owner**; no household share) |
| Open asset detail | Nickname, category, serial/identifiers, snapshots, lifecycle state, verification state |
| Register gear purchased elsewhere | Creates `customer_claimed` / unverified asset; staff verifies in backend |
| Limited update | **Editable:** nickname, notes, customer-visible photos/docs. **Not** shop-authoritative service completions or serial/category/verification |
| View portal-safe documents | Document visibility whitelist; Odoo attachment defaults for size/type in MVP |
| See shop-registered purchases | **Staff-seeded** verified assets on Tidewater demo partners (POS/sale auto-create later) |

### Explicitly deferred from first portal slice

- Service scheduling / booking UI and **service due/history portal UI** (registry-only MVP)
- Kit/configuration / trip readiness
- Auto-create from every POS sale (equipment Phase 3 — not required for Tidewater portal demo)
- Household multi-owner / commercial-child sharing
- Public catalog / ecommerce purchase of equipment
- Website migration of marketing content
- **Customer profile self-service** (address/phone/etc.) — separate later workstream (confirmed)
- App Store / custom Website themes beyond default + logo/colors
- Custom domain for sandbox demos

### Security (must ship with first portal code)

- `ir.model.access` for `base.group_portal` (tight create/write)
- Record rules: only own partner’s assets (and agreed share set)
- Attachment / `adventure.equipment.document` portal visibility flags
- HttpCase tests for isolation (cannot read another customer’s gear)
- No leakage of manager-only fields (e.g. purchase price)

### Staff workflow

Customer registers or edits → asset appears as **unverified / customer-claimed** → staff verifies serial/photos → `shop_verified` → authoritative for warranty/service ops (policy details follow equipment service phases).

---

## Auth and identity

| Topic | Decision / notes |
|-------|------------------|
| **User model** | Standard `res.users` portal users linked to customer `res.partner` |
| **Provisioning** | **Open self-signup** via `auth_signup` — any email may register. Staff may still create users from the backend as a convenience. |
| **Password reset** | Standard Odoo mail templates in production; Tidewater sandbox may rely on **seeded demo passwords** without outbound mail |
| **Multi-contact households** | **Out of MVP** — single `partner_id` owner only |
| **B2B / dive clubs** | Not required for Tidewater MVP; treat as later product decision if needed |
| **Staff impersonation** | Prefer real portal logins in Tidewater (seeded users) over impersonation tooling |
| **Partner matching** | Self-signup must resolve or create a partner cleanly so equipment `partner_id` ownership works; refine match/merge rules during build |
| **Sandbox credentials** | Fixed fictional passwords documented in [seed-data.md](../seed-data.md) |
| **Multi-company ACL** | Company-aware portal/equipment record rules from day one |

---

## Tidewater sandbox demonstration (end goal)

Once architecture is approved and modules exist, the shared **sandbox-diveshop** / Tidewater story should show:

1. **Pattern A, minimal public site:** Tidewater-branded **homepage** with shop identity, **Sign in**, and a clear path to the **equipment portal** (not a full marketing site yet).
2. At least **2–3 portal customers** with **fixed fictional passwords** documented in [seed-data.md](../seed-data.md).
3. Mix of equipment:
   - Shop-registered (staff-verified) gear “purchased at Tidewater” (**seeded**, not POS auto-create)
   - Customer-registered external gear pending verification
   - Service due/history **not** required on portal MVP
4. **Demo script (confirmed):** homepage → login → list gear → asset detail → register external item → staff verify in backend. Orders history, profile edit, and documents-only are **out of MVP demo scope**.

### Seed ownership (module-owned contributors)

| Data | Owner |
|------|--------|
| Website enabled, **minimal homepage**, menus (Home / Sign in / My Equipment), default theme + logo/colors | `adventure_website` contributor |
| Portal users + **documented fixed demo passwords** for story customers | `adventure_website` and/or `adventure_equipment_portal` contributor (reuse Tidewater partner XML ids) |
| Equipment assets / ownership / documents | `adventure_equipment` (+ scuba) Tidewater contributor |
| Orchestration | Existing `seed-tidewater` / sandbox bootstrap discovers contributors |

Normal `develop` deploys **do not** reseed; sandbox reset / explicit reseed loads portal demo state ([seed-data.md](../seed-data.md)).

---

## Suggested delivery slices (after design sign-off)

Complexity is relative (S/M/L), not calendar time. Ordering can adjust once open questions are answered.

| Slice | Purpose | Complexity | Depends on |
|-------|---------|------------|------------|
| **P0 — Architecture approval** | This document — **complete** (decisions closed) | S | — |
| **P1 — Website shell baseline (pattern A, minimal)** | `website`/`portal`; **`adventure_website`**; Tidewater **homepage** with login + equipment portal entry; default theme + logo/colors | S/M | Tenant can install Website; **may start before** `adventure_equipment` merge |
| **P2 — Equipment portal MVP** | `adventure_equipment_portal`: list/detail/register/limited edit + company-aware ACL + tests | L | **`adventure_equipment` on `develop`** |
| **P3 — Tidewater portal demo seed** | Portal users + fixed passwords + staff-seeded gear + demo runbook (homepage → login → gear) | M | P1 + P2 |
| **P4 — Branding / site polish** | Optional App Store theme, richer menus/pages, email template branding | S/M | P1 |
| **P5 — Sale/POS → portal continuity** | Purchased items appear automatically (equipment Phase 3 bridge) | M | Equipment POS/sale bridge |
| **Later** | Service booking, notifications, training portal, ecommerce, fuller marketing IA | — | Respective domain modules |

**Note:** Equipment staff registry / service / scuba may land from parallel PRs before P2; portal should not re-implement those models.

---

## Alignment with existing equipment roadmap

The equipment design already names **`adventure_equipment_portal`** as Phase 4 and lists portal open questions (household sharing, attachment quotas, verification SLA). This client-portal plan:

- **Confirms** that module as the first domain feature behind a shared Website/Portal shell.
- **Adds** the missing shell/branding layer (`adventure_website` + theme strategy) so equipment portal is not the only place that knows about Website.
- **Does not** change confirmed equipment decisions (customer equipment ≠ rental fleet; Community-first service; `adventure_equipment_service` ownership).

If equipment Phase 1–3B PRs are still merging, portal implementation should target the merged `adventure_equipment*` APIs, not fork draft branches long-term.

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Building a custom SPA “because portal looks dated” | Stick to Website/Portal + theme; improve QWeb UX incrementally |
| Theme forks that break on Odoo upgrades | Prefer App Store themes; minimize XPath overrides; semantic CSS |
| Portal ACL leaks (attachments, wrong partner) | Record rules + HttpCase from day one; document visibility flags |
| Blocking on website migration project | Keep migration out of scope; support hybrid subdomain portal |
| Demo without mail | Document sandbox mail setup or seed known portal passwords |
| Scope creep (full marketing site in MVP) | Pattern A confirmed, but **minimal homepage only** this stream; richer pages are later polish |
| Scope creep (training, ecommerce, service booking) | MVP = minimal homepage + equipment list/register/verify loop |
| Equipment code not yet on `develop` | Sequence portal build after registry merge; keep this doc branch docs-only until then |

---

## Open questions

**None remaining for this workstream.** All items below were resolved by explicit product decisions or by adopting the recommended defaults (now recorded in [Decisions confirmed](#decisions-confirmed-review)).

| # | Former question | Resolution |
|---|-----------------|------------|
| 1 | Hosting pattern A/B/C | **A**, minimal homepage |
| 2 | Tidewater demo journeys | Homepage → login → list → detail → register external → staff verify |
| 3 | Self-signup vs invite-only | Open self-signup |
| 4 | Profile editing | Separate later workstream |
| 5 | Theme strategy | Default Website + logo/colors |
| 6 | Create `adventure_website`? | **Yes**, in P1 |
| 7 | Sandbox custom domain? | Path-based only for MVP |
| 8 | Household sharing | Single `partner_id` owner |
| 9 | Editable fields | Nickname, notes, photos; serial/category/verification read-only |
| 10 | Service due/history in portal MVP? | **No** — registry-only |
| 11 | Document upload limits | Odoo defaults + visibility whitelist; tighten later if needed |
| 12 | Purchase linkage for demo | Staff-seeded verified assets |
| 13 | Sandbox credentials | Fixed fictional passwords in seed-data |
| 14 | Sandbox outbound email | Bypass acceptable for MVP demos |
| 15 | Multi-company rules | Company-aware from day one |
| 16 | Wait for `adventure_equipment`? | **Yes** for equipment portal |
| 17 | `adventure_website` before equipment merge? | **Yes** |
| 18 | Website migration dependency? | **None** |

---

## Adopted defaults (reference)

These were the recommended defaults; they are now **confirmed** (see decisions table). Kept here as a quick cheat sheet for implementers:

| Topic | Adopted default |
|-------|-----------------|
| Hosting / Tidewater pattern | **A — Odoo-hosted site**, **minimal homepage** |
| Theme | Default Odoo Website + Tidewater logo/colors |
| Shell module | Thin **`adventure_website`** |
| Auth | **Open self-signup** (`auth_signup`) |
| Equipment MVP | List / detail / register / limited edit; **no** service booking/history, orders, or profile edit |
| Purchases in demo | Staff-seeded verified assets |
| Household | Single `partner_id` owner |
| Sandbox access | Path-based URL; fixed demo passwords; mail bypass OK |
| Migration | No dependency |
| Sequencing | Website shell parallel; equipment portal after `adventure_equipment` on `develop` |

---

## Acceptance criteria for “architecture finalized”

- [x] Hosting pattern decided (**A**, minimal homepage MVP)
- [x] Tidewater demo customer journey decided
- [x] Portal signup decided (**open self-registration**)
- [x] Profile editing deferred to a **separate later workstream**
- [x] Remaining questions closed via recommended defaults
- [x] Module list agreed (`adventure_website` in P1; `adventure_equipment_portal` for equipment UX)
- [x] Tidewater credentials approach and gear seed approach agreed (fixed passwords; staff-seeded gear)
- [x] Dependency / sequencing agreed (shell parallel; portal after equipment merge)
- [x] Implementation warning updated (build in progress)
- [x] MkDocs / agent-rules references kept in sync for this planning page

---

## Next step after approval

1. ~~Kick off build~~ — **started:** `adventure_website` + `adventure_equipment_portal`.
2. Install/upgrade modules on Tidewater DBs and re-run `seed-tidewater` so portal users and homepage appear.
3. Smoke the demo path: homepage → login → My Equipment → register → staff verify.
4. When MVP is stable on sandbox, mark this page’s warning as shipped for P1/P2.