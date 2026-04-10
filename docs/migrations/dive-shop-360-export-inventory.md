# Dive Shop 360 — export surface inventory

**Status:** Discovery template — update as you confirm with vendor docs, sandbox access, or customer exports.

**Purpose:** Single checklist of everything Dive Shop 360 (sometimes shortened “D360”) can expose, so migration tooling and mapping stay complete.

Public-facing statements indicate shops can export **customer information**, **inventory records**, **sales reports**, and **certification data** before leaving the platform; inventory CSV export is described from **Office → Inventory → Products → Manage Products** (search, then **Action → Export**). Treat every row below as **to be verified** for your contract and product edition.

## How to use this table

For each **object**, confirm and record:

- **Path** — UI navigation or API endpoint.
- **Format** — CSV, XLSX, JSON, PDF-only, etc.
- **Cadence** — one-time full export, scheduled, manual only.
- **Limits** — row caps, date ranges, throttling.
- **Sample** — link or filename (stored **outside** repo if it contains PII; see [sample-exports-pii-and-retention.md](sample-exports-pii-and-retention.md)).

| Object / report | Path or API (TBD) | Format | Notes | Sample obtained (Y/N) |
|-----------------|-------------------|--------|-------|----------------------|
| Customers / contacts | | | Includes tags, marketing consent, tax IDs? | |
| Customer addresses | | | Multiple ship-to / bill-to? | |
| Products / SKUs | Office → Inventory → Products … Export (per public notes) | CSV (verify) | Variants, barcodes, categories | |
| Product categories / tags | | | | |
| On-hand quantities | | | By location? Serialized items? | |
| Cost / pricing fields | | | Map carefully to Odoo price lists / standard price | |
| Suppliers / vendor records | | | | |
| Purchase orders / receiving | | | | |
| POS / sales transactions | | | Line-level vs aggregated reports only | |
| Returns / refunds | | | | |
| Payments / tenders | | | Gift cards, store credit | |
| Gift cards / stored value | | | | |
| Layaways / deposits | | | | |
| Sales tax detail | | | Jurisdiction breakdown | |
| Certifications / training records | | | Agency, card number, dates | |
| Classes / courses / bookings | | | | |
| Employees / users | | | Usually re-created in Odoo; export for audit only | |
| Media / product images | | | URLs vs binary export | |
| Serialized / rental assets (if used) | | | Out of scope for Adventure v1 POS unless spike | |

## Gaps and follow-ups

- Confirm whether a **programmatic API** exists for your tier (vs CSV-only).
- Confirm **timezone and fiscal year** assumptions in date fields.
- List any **custom fields** the shop uses in D360 that must map to Odoo.

## References

- Shop-facing FAQ and product pages: [Dive Shop 360](https://diveshop360.com).
- Adventure target model direction: [core-model.md](../data-model/core-model.md).
