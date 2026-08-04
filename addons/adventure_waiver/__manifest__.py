# -*- coding: utf-8 -*-
{
    "name": "Adventure Waiver",
    "summary": "Generic signed-waiver CRM domain and partner matching for Adventure POS.",
    "version": "19.0.1.0.0",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_base", "contacts"],
    "data": [
        "security/waiver_security.xml",
        "security/ir.model.access.csv",
        "views/adventure_waiver_views.xml",
        "views/res_partner_views.xml",
        "views/menus.xml",
        "wizards/adventure_waiver_link_wizard_views.xml",
    ],
    "installable": True,
    "application": True,
}
