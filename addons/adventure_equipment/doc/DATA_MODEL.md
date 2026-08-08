# Data model reference

Phase 1 core models in `adventure_equipment`. For architecture and future modules, see [Equipment management](https://bsileo.github.io/adventure-pos-odoo/architecture/equipment-management/) and the [module README](../README.md).

## `adventure.equipment.asset`

Primary registry record for one physical item.

| Area | Key fields |
|------|------------|
| Identity | `name` (equipment number), `display_name`, `nickname`, `active`, `company_id` |
| Classification | `category_id`, `tag_ids` |
| Catalog (optional) | `product_id`, `product_tmpl_id`, `brand_name`, `manufacturer_name`, `model_name`, `manufacturer_sku`, `barcode` |
| Snapshots | `snapshot_product_name`, `snapshot_brand`, `snapshot_manufacturer`, `snapshot_model`, `snapshot_sku`, `snapshot_category` |
| Identifiers | `serial_number`, `asset_tag`, `manufacturer_registration`, `identifier_ids` |
| Ownership | `partner_id`, `ownership_type`, `ownership_verification_state`, `ownership_start_date`, `acquired_on`, `ownership_ids` |
| Acquisition | `acquisition_source`, `sold_by_this_shop`, `original_seller`, `purchase_date`, `purchase_price`, `origin_sale_ref`, `source_record_ref`, `data_provenance` |
| Lifecycle | `lifecycle_state`, `in_service_date`, `retired_on`, `retirement_reason`, `lost_on`, `disposition_on`, `lifecycle_notes` |
| Condition | `condition_state`, `condition_notes`, `condition_assessed_on`, `condition_assessed_by`, `condition_customer_reported`, `last_verified_on` |
| Warranty | `warranty_registered`, `warranty_lifetime`, `warranty_not_applicable`, `warranty_start_date`, `warranty_end_date`, `warranty_status` (computed), `warranty_registration_number`, `warranty_provider`, `warranty_notes` |
| Relations | `document_ids`, `event_ids`, `document_count` |
| Extension | `payload` (JSON), `customer_note`, `internal_note` |

Constraints: unique `name` per `company_id`; soft-unique serial per company + brand + model; product template/variant consistency; partner company alignment.

## `adventure.equipment.category`

Sport-agnostic taxonomy (not `product.category`).

| Field | Purpose |
|-------|---------|
| `name`, `code`, `sequence`, `active` | Label and ordering |
| `parent_id`, `parent_path`, `child_ids` | Hierarchy |
| `is_serviceable`, `is_durable` | Hints for future service modules |
| `company_id` | Optional; empty = shared across companies |
| `payload` | Extension JSON |

## `adventure.equipment.tag`

Simple labels for filtering and reporting (`name`, `color`, `active`, optional `company_id`).

## `adventure.equipment.identifier`

Additional or typed identifiers beyond the main serial field.

| Field | Purpose |
|-------|---------|
| `asset_id` | Parent equipment |
| `id_type` | serial, manufacturer_serial, shop_tag, barcode, rfid, manufacturer_registration, other |
| `name` | Value (trimmed on save) |
| `primary` | One primary per `id_type` per asset |
| `issuer`, `notes`, `date_recorded` | Metadata |
| `company_id` | Related from asset |

## `adventure.equipment.ownership`

Append-only ownership history.

| Field | Purpose |
|-------|---------|
| `asset_id`, `partner_id`, `company_id` | What and who |
| `date_from`, `date_to` | Ownership window |
| `change_type` | registration, sale, transfer, correction, migration |
| `is_current` | Exactly one current row per asset |
| `verification_state` | unverified, pending, verified, disputed |
| `notes`, `source_transaction_ref` | Context |

## `adventure.equipment.document`

Files and metadata attached to equipment.

| Field | Purpose |
|-------|---------|
| `asset_id`, `name`, `document_type` | image, receipt, warranty, manual, certification, inspection, other |
| `attachment_id` | `ir.attachment` (ondelete set null) |
| `issue_date`, `expiration_date`, `issuer` | Document metadata |
| `customer_visible`, `verified`, `notes` | Visibility and QA |
| `company_id` | Company scope |

## `adventure.equipment.event`

Read-only audit timeline (writes blocked except technical context).

| Field | Purpose |
|-------|---------|
| `asset_id`, `event_date`, `event_type`, `summary` | What happened |
| `payload` | Structured extra data |
| `user_id`, `company_id` | Who and where |

Event types include `registered`, `product_refreshed`, `ownership_transferred`, `lifecycle_changed`, `retired`, `reactivated`, and others.

## Partner extension

`res.partner.equipment_asset_count` — count of assets where `partner_id` equals that contact (contact-only; no parent rollup).
