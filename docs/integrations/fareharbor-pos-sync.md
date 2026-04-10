# FareHarbor ↔ Adventure POS — booking sync (design note)

**Status:** Draft — architecture and integration options. Implementation is tracked in GitHub Issues.

## Business scenario

- **POS** holds **customers** as `res.partner` in Odoo (see [core model](../data-model/core-model.md)).
- **FareHarbor** lists **tours and trips**; guests book through **FareHarbor’s website and ecosystem**, not through the POS checkout.
- **Goal:** when a booking is created or updated in FareHarbor, **sync a record into Adventure POS** so staff see it with the customer — a **system of record in Odoo**. This is not necessarily a duplicate POS order unless you add that explicitly later.

**Primary sync direction:** FareHarbor → Odoo (webhooks and/or scheduled jobs). Pushing Odoo customers into FareHarbor is optional later.

## Connecting bookings to POS customers

FareHarbor bookings include **customer/contact** data (name, email, phone, and typically a FareHarbor-side customer identifier in the API). Odoo already has **`res.partner`**. Define **identity resolution** up front:

1. **Stable external key (preferred):** store **`fareharbor_customer_id`** (or the exact field name from the API) on `res.partner` when known. Later bookings **link by this id**.
2. **Heuristic match:** normalized **email** (and optionally phone) to find an existing partner only if you accept collision risk; flag ambiguous matches for staff review.
3. **No match:** create a **new** `res.partner` or attach to a generic **guest** partner — an operational policy choice.
4. **Staff override:** allow **manual re-link** of a booking to a different partner when automation is wrong.

In-store POS identity (loyalty, house account) may not match FareHarbor; treat **FareHarbor customer id** and **email** as complementary signals.

## Proposed Odoo modeling (conceptual)

For a booking **record** without treating the sale as a POS transaction, a **dedicated model** is usually clearer than forcing `pos.order` in phase one:

| Concept | Purpose |
|--------|---------|
| `fareharbor.booking` (working name) | One row per FareHarbor booking; **immutable FareHarbor booking id** for idempotent upsert |
| `partner_id` | Resolved `res.partner`; smart button / chatter on the partner form |
| Trip / item reference | FareHarbor item id + display name; optional later link to `product.template` if trips mirror catalog |
| Dates, party size, status | From API — supports check-in and operations |
| `company_id` | Multi-company if applicable |
| Sync metadata | Last sync time; optional payload hash or raw JSON for support |

**Possible later extensions:**

- **`sale.order`** — if bookings should drive invoices or deposits in Odoo accounting.
- **`pos.order`** — rarely one-to-one with online FareHarbor bookings unless you add explicit check-in or upsell at the register.

## FareHarbor APIs and tools

- **External (Software Partner) API:** [FareHarbor Integration Center — External v1](https://developer.fareharbor.com/api/external/v1/) — OAuth 2.0, Bearer tokens; companies, items, availability, bookings, customers (exact scope per partner agreement).
- **Webhooks:** near-real-time booking lifecycle; use **idempotency** on booking id and FareHarbor’s verification rules. In Odoo: `http` route plus upsert into the booking model.
- **Alternatives:** Zapier / iPaaS for experiments; **middleware** if OAuth and webhooks should sit outside Odoo.

## Odoo integration surfaces

| Mechanism | Role |
|-----------|------|
| New module (e.g. `adventure_fareharbor`) | OAuth storage, HTTP client, field mapping |
| `ir.cron` | Backfill / polling if webhooks miss |
| `http` controllers | Inbound webhooks |
| `res.partner` extension | `fareharbor_customer_id` (and indexes as needed) |
| [Master catalog & sync](../architecture/master-catalog-and-sync.md) | Relevant only if FareHarbor **items** must align with governed catalog SKUs |

## Recommended decision path

1. Obtain **FareHarbor partner/API** access; confirm sandbox and booking + customer fields.
2. **Lock customer policy** — auto-create vs match-only; store FareHarbor customer id on partner; manual relink UX.
3. **Record shape** — `fareharbor.booking` + `partner_id` first; add `sale.order` only if finance needs it.
4. **Hosting** — all-in-Odoo vs middleware for OAuth and webhooks.
5. **Spike** — one booking upsert and partner resolution before any write-back to FareHarbor.

## Out of scope here

- **Fair Harbor** (apparel brand) — not the same as **FareHarbor** (bookings).
- Odoo core changes — stay under `addons/` per repository rules.
