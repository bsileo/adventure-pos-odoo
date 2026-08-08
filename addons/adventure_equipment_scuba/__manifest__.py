# -*- coding: utf-8 -*-
{
    "name": "Adventure Equipment Scuba",
    "summary": "Scuba vertical pack: cylinder VIP/hydro, regulator/BCD service defaults.",
    "version": "19.0.1.0.0",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "description": """
Adventure Equipment Scuba
=========================

Dive-shop vertical extension for customer-owned scuba equipment:

* Scuba service types (VIP, hydrostatic, regulator service, BCD service, …)
* Default category-targeted service policies
* Cylinder / regulator / scuba metadata on equipment assets
* Optional scuba fields on service records

Depends on the generic registry and service engine. Does not implement
portal, notifications, work orders, or POS bridges.
""",
    "depends": [
        "adventure_equipment_service",
    ],
    "data": [
        "data/scuba_service_type_data.xml",
        "data/scuba_service_policy_data.xml",
        "views/equipment_asset_views.xml",
        "views/service_record_views.xml",
    ],
    "demo": [
        "demo/demo_equipment_scuba.xml",
    ],
    "installable": True,
    "application": False,
}
