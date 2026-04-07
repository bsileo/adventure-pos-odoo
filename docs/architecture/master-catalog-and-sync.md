# Master Catalog and Tenant Sync

## Status

Draft v0.1 – Architecture for central catalog governance and distribution to operational tenant databases

## Purpose

This document defines how Adventure POS moves **approved** catalog data from the **master catalog environment** into **tenant operational databases**. It complements:

- [`docs/data-model/core-model.md`](../data-model/core-model.md) — responsibility split, product origin, sync metadata fields
- [`docs/data-model/product-catalog.md`](../data-model/product-catalog.md) — catalog layers, ingestion flow, release composition at a high level

**In scope:** release lifecycle, tenant targeting, field ownership and conflict rules, sync workflow semantics, deactivation policy, media approach, versioning and rollback concepts, failure handling.  
**Out of scope:** detailed vendor EDI field mappings, full UI/UX of import review, and implementation code paths (those belong in module design and PRs).

---

## 1. Environments and assumptions

### 1.1 Topology

| Environment | Role |
|-------------|------|
| **Master catalog** | Single (or explicitly documented) Odoo deployment where vendor feeds are ingested, canonical products are governed, **catalog releases** are built and published. |
| **Tenant operational** | One **database per shop** (tenant). POS, inventory, sales, purchasing, customers, local pricing, local suppliers, tenant-local products. |

### 1.2 Codebase

- The same **Adventure modules** are installed (or a documented subset) on master and tenant instances unless a deliberate exception is documented.
- **Odoo version parity** between master and tenants is assumed for sync unless the team documents a supported lag (avoid drift in `product` and related models).

### 1.3 Isolation model

- **Tenant isolation is primarily at the database boundary** (see core model doc). `res.company` remains meaningful inside each tenant DB for normal Odoo behavior; it is not the SaaS multi-tenant boundary across shops.

### 1.4 Transport (explicitly open in v0.1)

The physical mechanism that carries a published release from master to a tenant (e.g. authenticated API, export bundle + worker, queue, file drop) is an **implementation choice**. This document defines **required semantics** (idempotency, ordering, failure behavior); the transport layer must satisfy those semantics.

---

## 2. Identity and keys

### 2.1 Master stable identifiers

Every canonical product and variant in the master catalog that may sync to tenants must have a **stable master identifier** usable across releases:

- **Template-level** `master_catalog_id` (or equivalent) — unique in the master environment.
- **Variant-level** stable id — must map 1:1 to tenant `product.product` rows created from sync.

These identifiers are the **primary join keys** for idempotent create/update on the tenant.

### 2.2 Tenant product markers

On the tenant (aligned with core model):

| Concept | Purpose |
|---------|---------|
| `product_origin = master_sync` | Row originated from or is tied to master catalog sync. |
| `product_origin = tenant_local` | Row is owned by the shop; must not be overwritten or merged by master sync. |
| `master_catalog_id` (template and/or variant) | Links tenant row to master canonical record. |
| `master_sync_version` | Monotonic or comparable token for last successful application of master data (see §9). |

### 2.3 Local-only products

Products with `product_origin = tenant_local` **must be excluded** from master-driven upsert logic. Sync jobs should never change their identity or overwrite protected fields.

---

## 3. Catalog release model

### 3.1 Definitions

| Term | Meaning |
|------|---------|
| **Catalog release** | A versioned package of **approved** catalog changes ready for distribution. Not the same as a vendor file upload; releases are an output of governance. |
| **Release line / membership** | Association of a canonical master product (template and/or variant scope) to a release, possibly with line-level metadata (e.g. effective date, delta type). |
| **Publish** | Transition of a release to a state where it is eligible for tenant sync jobs. |
| **Distribution** | Assignment of which published content applies to which tenant DBs (see §4). |

### 3.2 Full vs incremental

- **Full (baseline)** — Suitable for new tenant provisioning or rebuild; expresses the desired catalog snapshot or a large superset as defined by release rules.
- **Incremental** — Contains only deltas since a prior baseline or prior release (create/update/deactivate). Reduces payload size; requires strict ordering and version compatibility.

Phase 1 may implement **one strategy** (often incremental on top of a stored baseline per tenant); the architecture should not assume infinite history without a retention policy.

### 3.3 Composition (master side)

Releases may be composed using criteria consistent with [`product-catalog.md`](../data-model/product-catalog.md) §119–133: vertical, brand, category, product family, tenant profile, explicit inclusion lists, pilot sets, etc. The master application enforces that **only approved** canonical rows enter a publishable release.

### 3.4 Overlapping releases

Multiple active release **channels** or **profiles** may exist (e.g. “Dive Core 2026” vs “Ski Accessories Base”). Targeting rules (§4) determine which tenants consume which releases. If a product appears in more than one applicable release, the implementation must define **precedence** (e.g. highest version wins, explicit merge, or last publish wins per product id). Document the chosen rule in the sync module; avoid silent ambiguity.

---

## 4. Tenant targeting

### 4.1 What “eligible” means

A tenant DB is **eligible** for a given published release if targeting rules match: business type, enabled release channel, explicit tenant allowlist, brand authorization, pilot/test flags, or equivalent configuration stored on master or in a small **tenant registry** (implementation detail).

### 4.2 New tenant provisioning

At a high level: create the tenant database, install modules, baseline company/warehouse/POS, register the tenant for master **targeting**, then run an **initial baseline sync**. Operational detail (hosting, checklists, upgrades, offboarding) lives in [`tenant-provisioning.md`](tenant-provisioning.md).

### 4.3 Ongoing sync

Published releases apply to eligible tenants on a **schedule or manual trigger**. Tenants may **lag** master; the system should record **last successfully applied release id / version** per tenant.

---

## 5. Field ownership matrix

Sync applies three classes of fields (see core model). This section fixes **behavior**, not only classification.

### 5.1 Master-owned fields

Examples: brand, category, product family, attributes and variant structure, trusted GTIN/UPC, base description, lifecycle status, canonical identifiers, base media references as defined by policy.

**Rule:** On sync, master values **overwrite** tenant values for these fields on `master_sync` products unless a documented **field-level exception** or **sync lock** applies (§6).

### 5.2 Tenant-owned fields

Examples: retail price, local active/inactive, supplier choice, local purchasing, local merchandising, POS-specific flags where local, local notes.

**Rule:** Master sync **must not** overwrite tenant-owned fields unless an explicit future “forced realignment” admin action exists and is audited.

### 5.3 Mixed / controlled fields

Examples: local SKU, display name supplements, department mapping, special-order flags, local sales descriptions.

**Rule:** Choose one default policy for phase 1 and document it in the sync module, for example:

- **Tenant wins after first sync** — master pushes initial value; later tenant edits preserved.
- **Master wins unless tenant locked** — use `sync_lock_state` or per-field lock for tenant overrides.

The matrix below is the **working default** for Adventure POS unless changed by ADR.

| Area | Owner | Sync behavior (default) |
|------|--------|-------------------------|
| Brand, category, family | Master | Overwrite on `master_sync` |
| Attributes / variant matrix | Master | Overwrite |
| Barcode / GTIN (trusted) | Master | Overwrite |
| Default code / internal reference (canonical) | Master | Overwrite if master is source of truth for that column |
| Description (base) | Master | Overwrite |
| Lifecycle / sellable state from master | Master | Overwrite or map to tenant `active` per §7 |
| Images (see §8) | Master | Replace per policy |
| List price / MSRP if used | Policy | Often master suggestion; tenant may own street price |
| Sales price / pricelist | Tenant | No overwrite |
| Supplier / vendor data | Tenant | No overwrite |
| `active` (tenant sellable) | Mixed | See §7 |

---

## 6. Conflict handling and `sync_lock_state`

### 6.1 When conflicts appear

Conflicts arise when:

- Master pushes an update while the tenant changed **mixed** fields, or
- Master changes structure (e.g. variant attributes) while tenant has stock or orders tied to old structure.

### 6.2 `sync_lock_state` (recommended)

Use a coarse or field-level lock concept on tenant products:

- **Unlocked** — Normal sync applies master-owned and mixed fields per policy.
- **Locked (partial or full)** — Tenant opts out of automatic master updates for protected fields or entire product; sync may still apply **critical** fixes (e.g. GTIN correction) if policy allows, with audit.

Exact granularity (template vs variant vs field JSON) is an implementation decision; phase 1 may use **template-level** lock only.

### 6.3 Structural changes

If master splits/merges variants or changes attribute definitions:

- Prefer **non-destructive** strategies: deactivate obsolete variants, create new ones with new master ids, migrate stock via explicit procedures.
- Destructive deletes during automated sync should be **avoided** or restricted to admin-approved releases.

---

## 7. Create, update, deactivate, delete

### 7.1 Create

When a release introduces a new master id not present in the tenant:

- Create `product.template` / `product.product` with `product_origin = master_sync`, set `master_catalog_id`, set `master_sync_version`.

### 7.2 Update

Apply master-owned field updates per §5–§6. Respect tenant-owned and locked fields.

### 7.3 Deactivate / discontinue (master-driven)

When master marks a product discontinued or removes it from a tenant’s effective catalog:

- **Preferred:** Set tenant **archive** or equivalent **inactive** for sales/POS per policy, preserve historical references on orders.
- **Hard delete** of products in tenant DBs is **risky** if any transactional row references exist; if used, must be an explicit, audited maintenance path—not default sync.

### 7.4 Local active flag

Tenants may hide a product locally (`active = False`) while master still lists it as active. Policy options:

- **Independent** — Tenant `active` is tenant-owned; master does not force visibility.
- **Master minimum** — Master discontinued forces tenant inactive regardless (override local display)

Pick one for phase 1 and document; **Independent** is often simpler for operations.

---

## 8. Media and attachments

### 8.1 Goals

- Consistent images/descriptions across shops where master governs branding.
- Avoid bloating tenant DBs with duplicate binaries if unnecessary.

### 8.2 Strategies (choose per implementation)

| Approach | Pros | Cons |
|----------|------|------|
| **URL references** (CDN or master public URLs) | Small tenant DB, easy updates | Network dependency; URL stability required |
| **Binary sync** to tenant attachments | Offline resilience | Storage and bandwidth; version churn |
| **Hybrid** | URLs with optional cache | More complex |

**Rule:** Define whether image updates are **release-bound** (new image = new release line) or **lazy-fetched** outside release cadence.

---

## 9. Versioning, ordering, and rollback

### 9.1 `master_sync_version`

Each tenant product (or template) should carry a **version token** after successful sync. Monotonic integers or content hashes of the applied payload are both acceptable if comparable.

### 9.2 Ordering

Tenant must apply releases in a **defined order** (monotonic release id or timestamp). Skipping or reordering without detection risks inconsistent state.

### 9.3 Rollback

Rollback is operational:

- **Forward fix** — Publish a corrective release (preferred).
- **Revert** — Restore tenant DB from backup or apply inverse delta if the system supports it (advanced; rarely phase 1).

Master should retain **release history** long enough to diagnose and issue corrective releases.

---

## 10. Sync job workflow (conceptual)

1. **Publish** release on master (immutable id).
2. **Compute** target tenant list for that release.
3. For each tenant (or batch):
   - **Fetch** last applied release / cursor.
   - **Build** applicable payload (full or delta).
   - **Apply** on tenant in a transaction where possible: create/update products, apply deactivations per §7.
   - **Record** success: release id, timestamp, counts, new `master_sync_version` watermark.
4. On failure: **retry** with backoff; **do not** partially advance cursor without recording state (see §11).

Idempotency: Re-applying the same release id with the same payload should not duplicate products or corrupt data (rely on `master_catalog_id` keys).

---

## 11. Failure handling and observability

### 11.1 Partial failure

- Failures should be **per-tenant** where possible so one shop does not block others.
- Persist **error reason**, **release id**, and **failing step** for support.

### 11.2 Retries

Transient network errors: retry. Data validation errors: **quarantine** that tenant’s job until fixed (bad mapping, schema drift).

### 11.3 Drift detection

If tenant module versions lag master assumptions, sync should **fail fast** with a clear message rather than corrupt data.

---

## 12. Phase 1 (MVP) vs later

### Phase 1 — Minimum viable

- Stable master and variant ids; `product_origin`, `master_catalog_id`, `master_sync_version`.
- One publish/subscribe path: **publish release → apply to eligible tenants**.
- Clear master vs tenant field split; conservative behavior on mixed fields (tenant wins or template-level lock).
- Deactivate/archive path for discontinued products; no destructive deletes by default.
- Basic audit log of applied releases per tenant.

### Later

- Incremental-only payloads with compaction and retention policies.
- Fine-grained field locks, richer conflict UI.
- Media CDN strategy with tenant caching and invalidation.
- Automated drift repair and admin “force realign” with audit.

---

## 13. Odoo implementation note

Custom work is expected in **master** modules (releases, import staging, canonical governance) and **tenant** modules (sync metadata fields, inbound API or worker, record rules for sync service users). Exact model names (`adventure.catalog.release`, etc.) should live in module manifests and technical specs; this document stays **architectural**.

---

## 14. Change control

Any change that affects **release semantics**, **targeting**, **field ownership**, **conflict behavior**, or **deactivation policy** should update this document and the related data-model docs in the same PR when practical.
