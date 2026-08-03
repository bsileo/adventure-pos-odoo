# -*- coding: utf-8 -*-
{
    "name": "Adventure Smartwaiver",
    "summary": "Smartwaiver provider connector for Adventure Waiver.",
    "version": "19.0.2.0.0",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_waiver", "base_setup"],
    "data": [
        "data/ir_cron.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
