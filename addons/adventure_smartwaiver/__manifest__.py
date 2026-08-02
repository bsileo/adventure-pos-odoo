# -*- coding: utf-8 -*-
{
    "name": "Adventure Smartwaiver",
    "summary": "Optional Smartwaiver signed-waiver sync into Adventure CRM.",
    "version": "19.0.1.0.1",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_base", "contacts", "base_setup"],
    "data": [
        "security/smartwaiver_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/smartwaiver_waiver_views.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/menus.xml",
        "wizards/smartwaiver_link_wizard_views.xml",
    ],
    "installable": True,
    "application": True,
}
