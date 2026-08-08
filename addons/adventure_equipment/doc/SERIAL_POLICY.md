# Serial number policy

## Soft uniqueness

Duplicate serial numbers are blocked when **all** of the following match another record in the same company:

- `serial_number` (case-insensitive, `=ilike`)
- `brand_name` (case-insensitive, when set)
- `model_name` (case-insensitive, when set)

Empty serial is allowed on any number of records.

## Same serial, different brand

Allowed — for example serial `12345` on Scubapro MK25 and serial `12345` on Apeks XTX50 in the same company.

## Same serial, same brand and model

Blocked with a generic validation message:

> A piece of equipment with this serial number already exists for this brand and model in your company.

The error does **not** include partner names, internal IDs, or other PII.

## Bypass for imports and migrations

Pass context `equipment_allow_duplicate_serial=True` on create/write to skip the constraint (technical / scripted use). Not exposed on standard forms.

## Primary identifier sync

When `serial_number` is set or changed, the module ensures one **primary** `adventure.equipment.identifier` row with `id_type` = `serial`, keeping the identifier list aligned with the main field.

## Related identifiers

Additional serials, shop tags, RFID, etc. live in `identifier_ids` with separate primary-per-type rules; the asset-level constraint applies only to `serial_number` + brand + model.
