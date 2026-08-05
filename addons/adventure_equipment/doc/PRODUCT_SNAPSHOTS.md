# Product link and snapshots

Equipment can optionally link to `product.product` / `product.template`. Catalog links use **ondelete set null** — deleting or archiving a product does **not** delete the equipment record.

## Blank-fill vs refresh

| Mechanism | Behavior |
|-----------|----------|
| **Create** with `product_id` | `_apply_product_defaults(overwrite=False)` — fills empty brand, model, SKU, barcode, snapshots, image |
| **Onchange** `product_id` (form) | Same blank-fill rules in the UI before save |
| **Refresh from product** (`action_refresh_product_defaults`) | `_apply_product_defaults(overwrite=True)` — overwrites catalog-derived fields and snapshots |

Changing `product_id` on an existing record via **write** updates `product_tmpl_id` but does **not** overwrite manually entered brand/model or existing snapshots unless you run **Refresh from product**.

## Snapshot fields

Persisted copies for reporting and display after catalog changes:

- `snapshot_product_name`
- `snapshot_brand`, `snapshot_manufacturer`, `snapshot_model`, `snapshot_sku`
- `snapshot_category`

Populated during blank-fill or refresh from product + category.

## ondelete set null

`product_id` and `product_tmpl_id` use `ondelete="set null"`. If the product is removed:

- Equipment remains **active** (unless staff archive it separately).
- Snapshot fields keep the last known catalog text.
- Lifecycle and ownership history are unchanged.

## Archive safety

Archiving a product (`active` = False) does **not** archive equipment. Staff may still see a link to the inactive product or an empty link after unlink, with snapshots intact.

## Product consistency

Validation ensures `product_id.product_tmpl_id` matches `product_tmpl_id` when both are set.
