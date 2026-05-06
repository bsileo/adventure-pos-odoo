# Scuba training and scheduling (future design)

!!! warning "Future / not implemented"

    This page is an **architecture and domain design** for multi-location scuba certification operations. It is **not** a description of shipped behavior. No accompanying training module is required to match this document until the team explicitly prioritizes implementation. Treat all model names as **proposals**.

**Audience:** Product, operations, and developers planning an operationally-first training layer on Adventure POS (similar in spirit to multi-site dive retail chains).

**Related today:** [`dive_shop_pos`](https://github.com/bsileo/adventure-pos-odoo/tree/develop/addons/dive_shop_pos) ships **seeds and POS vertical hooks only**—not this scheduling domain. [`adventure_rental`](https://github.com/bsileo/adventure-pos-odoo/blob/develop/addons/adventure_rental/models/rental_reservation.py) shows patterns for **state machines**, linking **`sale.order` / `pos.order`**, and **`fields.Json`** payloads. [Certifications and training migration](../migrations/certifications-training-migration.md) covers historical cert data, not this greenfield design. [FareHarbor POS sync](../integrations/fareharbor-pos-sync.md) illustrates **event-style records + JSON manifest + promote fields later**.

---

## Goals

- **One sellable course product** per certification program (e.g. Open Water Diver)—**no** duplication of SKUs per pool or location.
- **Operational training sessions** are separate, schedulable entities tied to that course: different dates, times, instructors, capacities, locations, and equipment needs.
- Students may attend sessions across **pools, classrooms, quarries, open water, and charters** based on availability, geography, staffing, makeup needs, or referrals.
- Design for **shop-floor reality**: weather, substitutions, no-shows, incomplete certifications, cross-location makeup, private instruction, accelerated classes.

---

## Design principles

1. **Sellable artifact ≠ operational schedule** — Commerce stays on Odoo **`product.template` / `product.product`**. Scheduling, staffing, and site logistics live in **dedicated training models**, not duplicated products.
2. **Sessions are first-class** — Date/time, site, capacity, roles, equipment, and compliance attach to the **session**, not to the product row.
3. **Enrollment is the hub** — The purchase creates or links an **enrollment**; attendance is modeled with **many registration rows** (including makeup and reschedule) with explicit lineage for reporting.
4. **Optional cohorts** — A **course run / cohort** can group sessions for marketing or coordination (“January OW group”) while still allowing **floating** session assignment and **cross-location** attendance.
5. **Extensibility** — Agency- or shop-specific attributes can live in **JSON** on enrollment or session lines until reporting needs justify **promoting** fields (same philosophy as the FareHarbor manifest design note).

---

## Suggested logical entities (proposed names)

| Concept | Role |
|---------|------|
| **Course (commercial)** | Odoo **product** for the cert program: price, taxes, POS availability; optional [master catalog](../data-model/product-catalog.md) sync metadata. |
| **Course template / program definition** | Non-sale metadata: agency, required **session types**, default ratios, eLearning flags. Links to the sellable product (1:1 or 1:n if multiple agencies share tooling). |
| **Session type** | Reference data: Academic, Confined water, Open-water checkout, charter block, etc.; drives progression gates and checklists. |
| **Training site / location** | Operational site: address, map links, arrival and parking notes, site caps, parking/check-in text. Prefer a **dedicated model** over abusing `res.partner` unless “partner as site” is standardized with clear categories. |
| **Session** | Scheduled instance: start/end, session type, site, min/max capacity, waitlist policy, staffing, equipment requirements, private/accelerated flags, status (scheduled / full / weather hold / cancelled / completed). Per-session: water conditions, required equipment, operational notes. |
| **Course run (optional)** | Coordinates a set of sessions; enrollments may optionally point here while makeup sessions remain attachable elsewhere. |
| **Enrollment** | One student’s lifecycle for a program + commercial line (`sale.order.line` or `pos.order.line`): progression state, agency candidate id, referral flags, restrictions. |
| **Session registration** | **Many per enrollment** — links a **session**; supports scheduled vs makeup vs no-show vs attended; instructor signoff; links to **supersedes** / **makeup_of** for audit and analytics. |
| **Instructor assignment** | Lead and assistants on a session; optional child model if substitution history must be fully audited. |
| **Equipment reservation** | Prefer extending **[`adventure_rental`](https://github.com/bsileo/adventure-pos-odoo/tree/develop/addons/adventure_rental)** so class logistics and rental pick/return stay one system. |
| **Waiver / compliance** | Early phases: documents + chatter; later: e-sign or vendor waiver with external ids on **enrollment**. |
| **Travel / charter event** | Optional specialization when a session is travel-heavy; relate to **session** without forcing all sessions through a trip system (future alignment with [FareHarbor](../integrations/fareharbor-pos-sync.md) or similar). |

Relationships to preserve:

- One **course / program** to many **sessions**.
- One **student enrollment** to many **session registrations**.
- Students may attend sessions across **locations**; makeup sessions need **not** be tied to the original schedule row beyond explicit lineage fields.

---

## Student assignment models

Support:

- **Staff assignment** after purchase.
- **Customer self-selection** of sessions (portal or in-shop).
- **Hybrid**: preferences with staff approval.

Store preferences (on enrollment or child records): preferred sites, days/times, travel radius, scheduling restrictions. An MVP typically uses **manual assignment** plus **validation** (capacity, prerequisites, ratios); **automated optimization** is a later constraint solver.

---

## Progression tracking

Recommended states (evolve with product): registered → academics started → academics completed → confined complete → open water complete → certified; plus **incomplete**, **makeup required**, referral paths.

- Partial completion is natural if **session types** gate progression.
- **Referral** and **incomplete** should be first-class; outbound referral artifacts can be documents + JSON until agency APIs exist.

---

## Capacity, waitlists, constraints

Per **session**: min/max seats, optional min to run, waitlist cap, computed open seats from confirmed registrations. **Waitlist** can be separate rows or a state on **session registration** with promotion rules (and optional customer confirmation windows if you add ecommerce).

---

## Instructor and resource management

Sessions should support lead instructor, assistants/DMs, pool lane or site allocation, **max student ratios**, and standards-compliance notes. **Substitutions** should be modeled (replacement staff, reason, timestamp) for audits.

---

## Automation and communications

Use **`mail.template`** with overrides by **session type** and **training site**. Triggers via **`base.automation`** on enrollment and session state/time. Pool-specific instructions, waiver reminders, packing lists, and instructor contact can merge from session and site records. SMS and weather integrations are **optional adapters**; start with manual **weather hold** on sessions if needed.

---

## Operational handling

The design explicitly accounts for: weather cancellations, pool availability changes, instructor substitutions, no-shows, incomplete certifications, makeup pools, cross-location attendance, private instruction, referral divers, and accelerated classes. **Bulk reschedule** flows should create new **sessions** and move **session registrations** while preserving history.

---

## Reporting and analytics

Denormalize report keys onto registration or enrollment lines (site, session type, instructor, company, session start). Attribute revenue carefully: either at **enrollment** for simplicity or define an agreed **allocation** rule for multi-session packages. Use SQL views or reporting models for utilization, conversion, no-shows, and rental attachment.

---

## Odoo module shape (when implemented)

Introduce a dedicated module (e.g. **`adventure_training`**) depending on `sale`, `contacts`, `calendar`, `mail`, and optionally `adventure_rental`, `sms`, `sign`, `hr`, `stock`. Keep heavy training logic **out** of thin vertical packs unless the team chooses to fold UI-only glue into [`dive_shop_pos`](https://github.com/bsileo/adventure-pos-odoo/tree/develop/addons/dive_shop_pos) (same module as today; still unrelated to this design until implemented).

**Phasing (suggested):**

1. Foundation — core models, access rules, staff scheduling UI, basic progression, email templates.
2. Operations depth — waitlists, substitutions, makeup, rental links, instructor permissions, reporting.
3. Customer-facing — portal selection / hybrid approval, SMS, waivers, weather hooks.
4. Integrations — agency or Dive Shop 360–style external ids, certification export, mobile instructor workflows, QR check-in.

---

## UX goals

- Reduce duplicate data entry (templates, copy-forward sessions).
- Support retail staff and instructors; mobile-friendly instructor flows as a phased goal.
- Stay flexible for real-world dive shop chaos without turning the product into a generic booking widget only.

---

## Future expansion

Reserve **external ids** for Dive360, agency APIs, trip integration, AI-assisted scheduling, and digital training records. See [core model](../data-model/core-model.md) for tenant and catalog boundaries.

---

## Sign-off

Design proposals in this document require **product and engineering review** before implementation. Update this page when the team ships an MVP or changes scope.
