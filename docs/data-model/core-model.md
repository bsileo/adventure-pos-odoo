# Adventure POS Core Data Model

## Status

Draft v0.3 – Single-Tenant Operational Databases with Central Master Catalog

## Architecture Direction

Adventure POS now assumes:
- one operational tenant per database
- one shared codebase across all tenants
- one central master catalog environment used to ingest, normalize, and govern catalog data
- a custom catalog distribution/sync process that moves approved catalog data into tenant databases

This replaces the earlier assumption of multiple independent shops sharing one operational database with runtime catalog-visibility rules.

## Why this direction was chosen

This approach:
- stays closer to standard Odoo behavior
- reduces POS/search/ecommerce visibility complexity
- reduces cross-tenant data leakage risk
- simplifies tenant operations and security
- allows shared application code while keeping business data isolated

## Responsibility Split

### Master Catalog Environment
Used for:
- vendor feed ingestion
- canonical product normalization
- category/brand/attribute governance
- external product references
- approval/review workflows
- catalog release preparation

### Tenant Operational Databases
Used for:
- POS
- sales
- purchasing
- inventory
- customers
- ecommerce later
- local pricing
- local vendor relationships
- tenant-local products

## Core Model Changes vs Prior Version

### Deployment and ownership
- tenant isolation now happens primarily at the database boundary
- `res.company` remains important inside each tenant DB, but is no longer the main SaaS tenant boundary

### Product model
Products in tenant DBs should distinguish:
- `product_origin = master_sync`
- `product_origin = tenant_local`

Recommended sync-related fields:
- `master_catalog_id`
- `master_sync_version`
- `sync_lock_state`

### Catalog visibility
The prior shared-db catalog rule model is removed from the operational core model.
Tenant DBs should not rely on runtime product visibility rules as the primary mechanism.
If a product is present in the tenant DB and active, it is generally visible subject to normal Odoo controls.

### Catalog support models
These are now primarily centered in the master catalog environment:
- External Product Reference
- Catalog Import Job
- Catalog Mapping Rule
- Canonical Product Template / Variant
- Catalog Release
- Release membership / release line model

### Tenant operational models
These remain tenant-local in each operational DB:
- Company
- Warehouse
- Stock Location
- Product Template / Variant
- Supplier Info
- Purchase Orders
- Sales Orders
- POS Config / POS Orders
- Inventory
- Customers

## Field Ownership Principle

For synced catalog data, each field should be classified as:
- master-owned
- tenant-owned
- mixed / controlled override

Examples likely to be master-owned:
- brand
- category
- product family
- attributes and variant structure
- UPC/GTIN where trusted
- lifecycle status
- canonical identifiers

Examples likely to be tenant-owned:
- retail price
- supplier choice
- local purchasing data
- local merchandising
- local website/POS visibility decisions
- local notes

## Related architecture

Master catalog releases, tenant targeting, sync semantics, and field-level behavior are defined in:
[`docs/architecture/master-catalog-and-sync.md`](../architecture/master-catalog-and-sync.md)
