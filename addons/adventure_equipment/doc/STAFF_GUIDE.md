# Staff guide — registering equipment

This guide covers day-to-day registration and maintenance of customer-owned equipment in **Adventure Equipment**.

## Open the registry

1. Go to **Equipment → Equipment** (or open a contact and use the **Equipment** smart button).
2. Click **New** to register a piece of gear.

Each record gets an equipment number (for example `EQ/00001`) automatically when you save.

## Register with a catalog product

Use this when the item exists in your product catalog (regulator, computer, BCD, etc.).

1. Set **Current Owner** to the contact who owns the gear.
2. Optionally pick **Product Variant** — brand, model, SKU, barcode, and snapshot fields fill **only where blank** (blank-fill).
3. Add **Serial Number**, **Category**, condition, warranty, and acquisition details as needed.
4. Set **Lifecycle State** to **Draft** while gathering information, then **Activate** when the record is ready for use.

To pull the latest catalog values into an existing record, use **Refresh from product** (overwrites catalog-derived fields).

## Register without a product

Use this for gear bought elsewhere, gifts, used equipment, or items not in your catalog.

1. Set **Current Owner** and **Category**.
2. Enter **Brand**, **Model**, and **Serial Number** manually.
3. Set **Acquisition Source** (for example **Other Shop**, **Used / Pre-owned**, **Gift**, **Customer Reported**).
4. Leave **Product Variant** empty — snapshots are taken from what you type.

## External purchase / not sold by this shop

- Set **Acquisition Source** to **Other Shop**, **Used / Pre-owned**, **Manufacturer**, **Gift**, or **Customer Reported** as appropriate.
- Fill **Original Seller** and **Purchase Date** when known.
- **Sold by This Shop** is computed automatically when source is **Sold by This Shop**; use **Origin Sale Reference** for a human-readable receipt or order name (typed link to `sale.order` / POS is deferred).

## Serial numbers

- Enter the serial on the asset form; a primary **Serial** identifier row is created automatically.
- Duplicate serials for the same **company + brand + model** are blocked (case-insensitive). Different brands may share the same serial string.
- Managers can bypass duplicates only via technical context `equipment_allow_duplicate_serial` (imports/migrations), not from the standard UI.

## Transfer ownership

1. Open the equipment record.
2. Click **Transfer Ownership** (wizard).
3. Choose the new owner, transfer date, reason, and verification state.
4. Confirm — **Current Owner** updates and a new row is appended to **Ownership History**; the previous row is closed.

Direct edits to **Current Owner** also sync history (same as a transfer).

## Activate, retire, and archive

| Action | What it does |
|--------|----------------|
| **Activate** | Moves lifecycle to **Active**; sets **In Service Date** if empty. |
| **Retire** | Sets lifecycle to **Retired** and **Retired On**; record stays active in the database and history is preserved. |
| **Archive** (`active` = off) | Hides the record from default lists; **does not** change lifecycle state. Use for duplicates or obsolete rows you want out of the way without retiring gear still in service. |

**Do not** use **Delete** except for draft records with no documents and no ownership/event history beyond the initial registration. For real gear, **Retire** or **Archive** instead.

## Ownership type

- **Customer** — default; owned by an individual contact.
- **Organization** — owned by a company partner (club, team).
- **Shop** — shop-held customer gear (rare in Phase 1; full shop-inventory flows are deferred).

## Verification

Set **Ownership Verification** to **Unverified**, **Pending**, **Verified**, or **Disputed** as you confirm provenance. Transfers can update this state on the new history row.

## Related documentation

- [Data model](DATA_MODEL.md)
- [Lifecycle](LIFECYCLE.md)
- [Ownership](OWNERSHIP.md)
- [Import](IMPORT.md)
