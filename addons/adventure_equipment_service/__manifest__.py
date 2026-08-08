# -*- coding: utf-8 -*-
{
    "name": "Adventure Equipment Service",
    "summary": "Generic service lifecycle, policies, and forecasting for customer equipment.",
    "version": "19.0.1.0.0",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "description": """
Adventure Equipment Service
===========================

Sport-neutral service engine for customer-owned equipment:

* service types
* maintenance policies
* materialized requirements and date aging
* completed service records
* overrides, waivers, and asset service rollups

Scuba-specific rules belong in adventure_equipment_scuba (Phase 3B).
""",
    "depends": [
        "adventure_equipment",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/equipment_service_record_rules.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "data/service_type_data.xml",
        "views/service_type_views.xml",
        "views/service_policy_views.xml",
        "views/service_requirement_views.xml",
        "views/service_record_views.xml",
        "views/equipment_asset_views.xml",
        "views/res_partner_views.xml",
        "views/menus.xml",
        "wizards/service_override_wizard_views.xml",
        "wizards/service_waiver_wizard_views.xml",
        "wizards/service_complete_wizard_views.xml",
    ],
    "demo": [
        "demo/demo_equipment_service.xml",
    ],
    "installable": True,
    "application": False,
}
