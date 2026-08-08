# -*- coding: utf-8 -*-
{
    "name": "Adventure AI",
    "summary": "AdventurePOS AI runtime: providers, capability registry, sessions, metering.",
    "version": "19.0.1.0.0",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_base", "base_setup"],
    "data": [
        "security/ai_security.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter_data.xml",
        "views/ai_session_views.xml",
        "views/ai_usage_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": True,
}
