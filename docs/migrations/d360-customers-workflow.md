# D360 customers workflow

**Status:** First-pass workflow for the Adventure D360 migration addon.

**Purpose:** Define the operator-facing workflow for taking a Dive360 customer/contact export, preprocessing it, reviewing mixed partner types, and upserting into `res.partner`.

## Scope

This workflow is intentionally broader than a pure retail-customer import.

The observed D360 contact export includes:

- individual people
- companies and organizations
- vendors and manufacturers
- other partner-like contacts

The workflow therefore treats the file as a **partner import**, but rows that remain `ambiguous` after classification are held back for operator review instead of being imported with a guess.

## First supported source file

The current workflow is designed around the flat CSV shape seen in files like:

```text
contact_list_<timestamp>.csv
```

Observed source columns include:

- `Customer ID`
- name fields
- address fields
- phone fields
- `Email Address`
- `Birthday`
- `Customer Type`
- `Invoice Type`
- `Last Purchase Date`

The raw export may also contain `Social Security Number`. The workflow must **not** import SSN into Odoo.

## Operator flow

### 1. Obtain the D360 export

- Run the D360 customer/contact export that produces the flat contact list CSV.
- Keep the original filename and note who ran the export and when.
- Store the raw export in an approved working location; do not commit raw PII exports to git.

### 2. Upload and preprocess

- Open the `D360 Migration` workflow in Odoo.
- Start `New customer workflow`.
- Upload the original CSV file.
- Record any source notes, such as the D360 menu path, operator, export time, or cutover context.

### 3. Review classification and quality flags

The preprocessing step should classify rows into:

- `person`
- `company`
- `ambiguous`

The review screen should also flag:

- duplicate `Customer ID` values inside the file
- weak or mixed partner-type signals
- malformed or low-information rows

### 4. Upsert partners

- Upsert rows into `res.partner` using the stable D360 source identity.
- Skip rows whose partner kind is still `ambiguous`; leave their import status at `Pending` until an operator resolves them.
- Initial key: `Customer ID`
- Initial external reference format: `d360.partner.{Customer ID}`

### 5. Validate the result

- Compare source row count against imported rows.
- Spot-check both person-style and company-style partner records.
- Re-run the same file to verify the upsert path is idempotent.

## First-pass classification policy

### Person indicators

- plausible `First Name` and `Last Name`
- `Gender` of `Male` or `Female`
- valid `Birthday`
- consumer email domains
- `Retail` customer or invoice type

### Company indicators

- blank `First Name` with an organization-style name in `Last Name`
- brand or business keywords such as `Inc`, `LLC`, `Scuba`, `Dive`, `Aquatics`
- role mailboxes like `sales@`, `info@`, `orders@`, `operations@`

### Ambiguous indicators

- weak, mixed, or conflicting signals
- incomplete rows that cannot be safely classified

Classification should guide review and default import behavior, but it must **not** replace the D360 source ID as the upsert key. If classification remains `ambiguous`, the row should stay `Pending` rather than being inserted into `res.partner`.
