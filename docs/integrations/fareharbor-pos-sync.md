# FareHarbor ↔ Adventure POS — booking sync (design note)

**Status:** Draft — architecture and integration options. Implementation is tracked in GitHub Issues.

## Business scenario

- **POS / CRM** holds **customers** as `res.partner` in Odoo (see [core model](../data-model/core-model.md)). Adventure OS is the **system of record** for ongoing customer relationships; FareHarbor bookings **feed** that CRM. Synced partners and booking records are **tenant-local** in each operational database like other customers, not master-catalog objects.
- **FareHarbor** lists **tours and trips**; guests book through **FareHarbor’s website and ecosystem**, not through the POS checkout.
- **Goal:** when a booking is created or updated in FareHarbor, **sync a record into Adventure POS** so staff see it with the right **customer** and **manifest** detail. This is not necessarily a duplicate POS order unless you add that explicitly later.

**Primary sync direction:** FareHarbor → Odoo (webhooks and/or scheduled jobs). Pushing Odoo customers into FareHarbor is optional later.

## FareHarbor concepts (what we are mapping)

### Contact vs manifest (booker vs participants)

- **Contact (booker):** the person attached to the booking for communication and payment. Maps to **one** `res.partner` in Odoo using the CRM policy below.
- **Manifest / participants:** per line item (e.g. “Certified Diver”), the **passengers** on the trip — names, waivers, certification, and **shop-configured custom fields**. These can differ from the contact (e.g. one person books for several divers). They are **not** the same as the contact record; do not collapse them into `partner_id` by default.

### Duplicate contacts in FareHarbor

FareHarbor does **not** enforce unique contacts. Multiple contact rows can share the same name, email, and phone. **Odoo CRM** instead uses **normalized email** (plus a mapping of every FareHarbor contact id) so one real-world customer does not become many duplicate partners.

### Internal vs customer-facing fields

FareHarbor items may include **internal-only** fields (staff pricing, check-in notes, etc.) alongside **guest-facing** questionnaire fields. Both can be stored on the booking or participant records; **guest-facing** answers are the usual “green box” manifest data. Prefer **staff-only access** in Odoo for internal fields when exposed by the API.

In **V1 JSON**, keep a clear split: e.g. a nested object or key prefix such as `internal.*` (or `guest.*` / flat stable ids from the API) so imports and future migrations can tell operational fields apart from manifest answers. **Field-level security** applies once specific keys are promoted to real columns; in V1 you may restrict the **participant line form or JSON viewer** to staff groups if sensitive operational data is present in the payload.

## Partner resolution — CRM-first (`res.partner`)

**Policy:** resolve the **booking contact** to a **single** `res.partner` by **normalized email** when an email is present. **Do not** treat FareHarbor contact id as 1:1 with `res.partner` — FH may create a new contact row for the same person.

**Required companion:** a **many-to-one mapping** of FareHarbor contact ids → `res.partner` (e.g. `fareharbor.contact.mapping` with `fh_contact_id`, `partner_id`). **Every** contact id seen from the API for that person must be recorded so sync stays **traceable** and **idempotent** when FH rotates or duplicates contact rows.

**Resolution steps:**

1. **Normalize email** (lowercase, trim; define policy for `+tags` if needed).
2. **Lookup** `res.partner` by normalized email; if none, **create** a partner.
3. On each sync, if the payload includes a **new** `fh_contact_id` for that email, **add a mapping row** — do **not** create a second partner.
4. **Update** name/phone on the partner using agreed rules (e.g. latest booking, non-empty wins, or staff override).

**Staff:** allow **manual re-link** of a booking to a different partner when automation is wrong.

**Risks and mitigations:**

| Risk | Mitigation |
|------|------------|
| Shared inbox (family, assistant, company email) | Manual split/relink; optional flag to suppress auto-merge for known addresses |
| No email on FH contact | Create or match with lower confidence (e.g. phone + name); flag for review (e.g. chatter or activity); never invent email |
| Same person, two emails | Two partners until staff merge; optional duplicate reports (name + phone) |
| Marketing / consent | Sync FH flags into Odoo; CRM is source of truth for how you use them |

In-store POS identity (loyalty, house account) may still diverge from FareHarbor; the **mapping table** and **email** are the primary link for online booking contact data.

**Design alternative (reference, not the CRM default):** one `res.partner` per FareHarbor contact id gives maximum parity with FH’s graph but duplicates CRM cards when FH duplicates contacts. Use only if audit parity outweighs CRM deduplication.

## Proposed Odoo modeling (conceptual)

For a booking **record** without treating the sale as a POS transaction, a **dedicated model** is usually clearer than forcing `pos.order` in phase one:

| Concept | Purpose |
|--------|---------|
| `fareharbor.booking` (working name) | One row per FareHarbor booking; **immutable FareHarbor booking id** for idempotent upsert |
| `partner_id` | `res.partner` for the **booking contact** (booker), resolved via CRM policy above |
| `fareharbor.contact.mapping` (working name) | Rows: `fh_contact_id` → `partner_id`; supports many FH contact ids per partner |
| Participant lines (child of booking) | One row per FH line / manifest slot (e.g. each diver); holds **V1 manifest payload** (below) |
| Trip / item reference | FareHarbor item id + display name; optional later link to `product.template` if trips mirror catalog |
| Dates, party size, status | From API — supports check-in and operations |
| `company_id` | Multi-company if applicable |
| Sync metadata | Last sync time; optional payload hash or raw JSON fragment for support |

**Participant / manifest (V1/MVP):** shop-specific custom fields differ per dive operation. **Do not** add a fixed Odoo field per FH question in core. On each **participant line**, store:

- A **JSON** field (`fields.Json` or equivalent) with **all** guest-facing answers and structured API data for that line, keyed by **stable** FareHarbor field ids or API keys (not only display labels).

**Reporting (V1):** treat detailed reporting on specific manifest keys as **out of scope** unless you add database/SQL views over JSON or promote fields post-MVP.

**Optional:** raw API substring on booking or line for debugging; retention policy as needed.

**Later:** after reviewing real data, **promote** selected keys to **real Odoo fields** on the participant model, **update the integration** to fill them, and run a **one-time idempotent migration** from existing JSON into those columns (optionally **dual-write** JSON + columns for a transition).

**Optional on participant line:** link to `res.partner` when you intentionally match a known diver (manual or future matcher).

**Possible later extensions:**

- **`sale.order`** — if bookings should drive invoices or deposits in Odoo accounting.
- **`pos.order`** — rarely one-to-one with online FareHarbor bookings unless you add explicit check-in or upsell at the register.

## FareHarbor APIs and tools

- **External (Software Partner) API:** [FareHarbor Integration Center — External v1](https://developer.fareharbor.com/api/external/v1/) — OAuth 2.0, Bearer tokens; companies, items, availability, bookings, customers (exact scope per partner agreement).
- **Webhooks:** near-real-time booking lifecycle; use **idempotency** on booking id and FareHarbor’s verification rules. In Odoo: `http` route plus upsert into the booking model.
- **Alternatives:** Zapier / iPaaS for experiments; **middleware** if OAuth and webhooks should sit outside Odoo.

**Confirm before implementation:** exact identifiers for **booking contact** vs **line-item / manifest** data in API and webhook payloads (whether manifest appears as nested customers, custom-field answers per item, etc.).

## Odoo integration surfaces

| Mechanism | Role |
|-----------|------|
| New module (e.g. `adventure_fareharbor`) | OAuth storage, HTTP client, field mapping |
| `ir.cron` | Backfill / polling if webhooks miss |
| `http` controllers | Inbound webhooks |
| `res.partner` extension | CRM fields as needed (e.g. normalized email helper); **not** a single sole `fareharbor_customer_id` — use **mapping model** for all FH contact ids |
| `fareharbor.contact.mapping` | `fh_contact_id` → `partner_id` |
| Participant line model | JSON manifest field (V1); optional promoted fields later |
| [Master catalog & sync](../architecture/master-catalog-and-sync.md) | Relevant only if FareHarbor **items** must align with governed catalog SKUs |

## Recommended decision path

1. Obtain **FareHarbor partner/API** access; confirm sandbox and **booking + contact + line-item/custom-field** shapes in payloads.
2. **Implement** `fareharbor.booking` + participant lines with **JSON manifest**; **partner resolution** by email + **contact mapping** table.
3. **Spike** — one booking upsert, partner resolution, and participant JSON round-trip before write-back to FareHarbor.
4. **Hosting** — all-in-Odoo vs middleware for OAuth and webhooks.
5. **Post-MVP** — promote high-value manifest keys to stored fields + migration when requirements are clear.

## Out of scope here

- **Fair Harbor** (apparel brand) — not the same as **FareHarbor** (bookings).
- Odoo core changes — stay under `addons/` per repository rules.
