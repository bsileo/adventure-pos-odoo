# -*- coding: utf-8 -*-
{
    "name": "Adventure Equipment Configuration",
    "summary": "Customer packing lists and equipment configurations.",
    "version": "19.0.1.0.1",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "description": """
Adventure Equipment Configuration
=================================

Customer-owned packing lists and equipment configurations (setups)
referencing adventure.equipment.asset records.

Portal UX lives in adventure_equipment_configuration_portal.
""",
    "depends": [
        "adventure_equipment",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/equipment_configuration_record_rules.xml",
        "views/equipment_configuration_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
}
