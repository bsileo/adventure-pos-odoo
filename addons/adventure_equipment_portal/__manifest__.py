# -*- coding: utf-8 -*-
{
    "name": "Adventure Equipment Portal",
    "summary": "Customer portal for viewing and registering owned equipment.",
    "version": "19.0.1.0.2",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "description": """
Adventure Equipment Portal
==========================

Customer self-service for customer-owned equipment:

* My Equipment list and detail
* Register gear purchased elsewhere (pending staff verification)
* Limited edits: nickname, customer notes, avatar image
* Portal ACL + partner-scoped record rules

Depends on adventure_equipment (staff registry) and adventure_website (shell).
""",
    "depends": [
        "adventure_equipment",
        "adventure_website",
        "portal",
        "website",
        "auth_signup",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/equipment_portal_record_rules.xml",
        "views/equipment_portal_templates.xml",
    ],
    "installable": True,
    "application": False,
}
