# Adventure POS Product Catalog Model

## Status

Draft v0.2 – Master Catalog and Tenant Database Distribution Model

## Architecture Direction

Adventure POS now assumes:
- a master catalog Odoo environment for catalog governance
- one operational tenant per database
- a shared codebase across all environments
- a custom catalog distribution/sync mechanism from master to tenant databases

This replaces the earlier concept of runtime tenant catalog visibility rules inside one shared operational database.

## Catalog Philosophy

### Canonical products are the internal source of truth
Vendor feeds should be normalized into canonical products in the master environment.

### Distribution is upstream, not runtime
The question is no longer:
- should tenant X see this product right now inside a shared database?

The new question is:
- should this product be included in tenant X’s next catalog release or sync?

### Product presence in a tenant DB determines baseline visibility
If the product is synced into the tenant DB and active, it is generally available subject to ordinary Odoo controls.

### Tenant-local products remain first-class
Tenants must be able to create products that are not part of the shared central catalog.

## Catalog Layers

1. External source layer
   - vendor CSV
   - portal export
   - API feed
   - manual spreadsheet

2. Normalized import layer
   - mapping rules
   - normalization
   - staging rows
   - candidate matching

3. Canonical product layer
   - master catalog products
   - canonical variants
   - brand/category/attribute governance

4. Catalog release layer
   - approved products grouped into release packages
   - full or incremental releases
   - vertical-specific releases

5. Tenant distribution layer
   - which release content goes to which tenant DBs

6. Tenant local product layer
   - products created directly in tenant DBs

## Recommended Catalog Models

### In the master catalog environment
- Brand
- Product Category
- Product Attribute / Value
- Canonical Product Template
- Canonical Product Variant
- External Product Reference
- Catalog Import Job
- Catalog Import Line / Staging Row
- Catalog Mapping Rule
- Catalog Release
- Catalog Release Line / Membership

### In tenant operational databases
- Product Template / Variant
- Supplier Info
- local pricing data
- local merchandising data
- tenant-local products

## Product Types

### Canonical master product
A centrally governed product record managed in the master catalog environment.

### Synced tenant product
A tenant-database product created or updated from a canonical master product.

Recommended sync metadata:
- `product_origin = master_sync`
- `master_catalog_id`
- `master_sync_version`

### Tenant-owned local product
A tenant-database product created locally and protected from master sync overwrite.

Recommended local marker:
- `product_origin = tenant_local`

## Vendor Ingestion Flow

Vendor Feed Received
→ Catalog Import Job Created
→ Rows Loaded into Staging
→ Normalization + Mapping Rules Applied
→ Match Against Existing Canonical Products
→ Create / Update / Ignore / Review Decision
→ External Product References Updated
→ Approved Canonical Products Added to Catalog Release
→ Release Published for Distribution
→ Tenant Sync Jobs Apply Release to Tenant Databases

## Catalog Release and Distribution

A release may be composed by:
- vertical
- brand
- category
- product family
- tenant profile
- explicit inclusion list

Examples:
- Dive Core Spring 2026
- Ski Accessories Base Release
- Shared Cross-Vertical Essentials
- Pilot Release for Beta Tenants

Tenant distribution may be determined by:
- business type
- enabled release channel
- explicit tenant assignment
- brand authorization
- pilot/test status

## Field Ownership Model

### Likely master-owned
- brand
- category
- product family
- attributes and variant structure
- UPC/GTIN where trusted
- base description
- lifecycle status
- base images/media references
- canonical identifiers

### Likely tenant-owned
- retail price
- active/inactive locally
- supplier choice
- local purchasing data
- local merchandising
- website visibility
- POS-specific behavior
- local bundles
- local notes

### Mixed / controlled
- local SKU
- local display name supplements
- local department mapping
- special-order flags
- local sales descriptions

## Key Workflow Examples

### New vendor feed enters master catalog
- import
- normalize
- match
- create/update canonical products
- add approved changes to release
- publish release
- sync eligible tenants

### New tenant is provisioned
- create tenant DB
- install shared modules and baseline config
- assign release channel or profile
- run initial catalog sync

Operational steps and lifecycle (hosting, upgrades, offboarding): [`docs/architecture/tenant-provisioning.md`](../architecture/tenant-provisioning.md).

### Tenant creates a local product
- create product in tenant DB
- set `product_origin = tenant_local`
- exclude from overwrite behavior during sync

## Related architecture

Release model, field ownership matrix, sync workflow options, create/update/deactivate rules, conflict handling, media strategy, and rollback/versioning:
[`docs/architecture/master-catalog-and-sync.md`](../architecture/master-catalog-and-sync.md)
