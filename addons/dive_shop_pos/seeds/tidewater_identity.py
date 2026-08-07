# -*- coding: utf-8 -*-
"""Canonical Tidewater Dive Shop identity for demo / sandbox seed data.

Tidewater is the fictional sandbox dive shop (sandbox-diveshop story tenant):
Pittsburgh, PA — used for shared demos, QA, and deterministic seed scenarios.

The seed rebrands the database main company (`base.main_company`). It must not
create a second `res.company` for Tidewater.

When adding modules or user-visible functionality, extend the Tidewater seed
pack so the feature is testable and demonstrable after seed (see agent-rules).
"""

TENANT_SLUG = "shop_tidewater"
COMPANY_XML_ID = "company_tidewater"
SEED_PROFILE = "tidewater"
# Older profile names still load the same pack.
LEGACY_SEED_PROFILES = ("tideledger", "dive_shop")

COMPANY_NAME = "Tidewater Dive Shop"
COMPANY_EMAIL = "ops@tidewater.example"
COMPANY_PHONE = "+1 555-0412"
COMPANY_STREET = "412 North Shore Drive"
COMPANY_CITY = "Pittsburgh"
COMPANY_ZIP = "15212"
COMPANY_STATE_CODE = "PA"
COMPANY_COUNTRY_CODE = "US"

# Prior company XML ids from earlier seed branding; migrate in place.
LEGACY_COMPANY_XML_IDS = (
    "company_tideledger",
    "company_adventure_dive_center_dev",
)
