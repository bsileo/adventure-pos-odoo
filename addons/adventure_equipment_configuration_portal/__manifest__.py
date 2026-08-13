# -*- coding: utf-8 -*-
{
    "name": "Adventure Equipment Configuration Portal",
    "summary": "Customer portal for packing lists and equipment configurations.",
    "version": "19.0.1.0.5",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "description": """
Adventure Equipment Configuration Portal
========================================

Portal self-service for packing lists and configurations:

* /my/equipment/lists — checklist UX with free-text add + equipment autocomplete
* Loose suggest search across name, category, brand/model, notes, and related fields
* Line check / edit free-text / remove / up-down reorder / hard delete
* Broken-reference indicators when equipment is unavailable

Depends on adventure_equipment_configuration and adventure_equipment_portal.
""",
    "depends": [
        "adventure_equipment_configuration",
        "adventure_equipment_portal",
        "portal",
        "website",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/equipment_configuration_portal_record_rules.xml",
        "views/equipment_configuration_portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "adventure_equipment_configuration_portal/static/src/css/checklist.css",
            "adventure_equipment_configuration_portal/static/src/interactions/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
