# Sample exports, PII, parallel-run, and retention

## Sanitized sample exports (pilot and edge cases)

**Goal:** Validate parsers and mappings without leaking real customer data into git or shared drives.

### What to collect

- **Small shop** — few hundred products, simple tax.
- **Large catalog** — performance and row-limit testing.
- **Messy variants** — ambiguous barcodes, duplicate names, discontinued mixed with active.
- **International** — non-US addresses, phone formats, encoding (UTF-8 vs legacy).
- **Tax edge cases** — exempt customers, multi-rate jurisdictions if applicable.

### Handling rules

- **Do not commit** raw exports that contain PII or financial detail. Use redacted fixtures if anything is checked in (fake names, truncated IDs).
- Store working copies in **approved** locations (encrypted share, customer-specific vault) per your security policy.
- Label files with **source shop id**, **export date**, and **D360 version** if known.

### Redaction checklist (if creating repo-safe samples)

- [ ] Replace names, emails, phones, addresses with synthetic data
- [ ] Truncate or hash government identifiers
- [ ] Remove or scramble internal account numbers not needed for parser tests

## Parallel-run and retention policy

Define these **per engagement** and record in the project file or SOW.

### Parallel run

- **Freeze window** — When D360 stops accepting new transactions before cutover (typically short: hours to one business day).
- **Read-only period** — How long the shop may still **log into D360 read-only** for lookups (cert history, dispute resolution). Set an end date.
- **Source of truth** — After go-live, **Odoo** is authoritative for new operations; D360 is archive-only.

### Accounting ownership

- **Who reconciles** the straddle period (last D360 close vs first Odoo books)?
- **Cutover journal entries** — Opening balances and inventory — prepared by shop accountant or implementation partner; document sign-off.

### Data retention

- How long **full D360 exports** are retained (contractual / legal).
- Whether **Odoo backups** supersede need for D360 access after N months.

### Contacts

| Role | Name | Responsibility |
|------|------|----------------|
| Shop owner | | Approves freeze and go-live |
| Accountant | | Opening balances, GL |
| Implementation | | Imports, validation report |
