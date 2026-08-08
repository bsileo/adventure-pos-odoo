# -*- coding: utf-8 -*-
{
    "name": "Adventure Website",
    "summary": "Minimal Odoo Website shell for AdventurePOS customer portals.",
    "version": "19.0.1.0.1",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "description": """
Adventure Website
=================

Thin Website + Portal shell for pattern A (Odoo-hosted shop site):

* Enables Website / Portal / open self-signup
* Minimal public homepage with Sign in / Sign up and portal entry
* Company-branded chrome (default theme + res.company logo/colors)
* Tidewater demo seed hooks for website configuration

Domain features (equipment, etc.) live in adventure_*_portal modules.
""",
    "depends": [
        "adventure_base",
        "website",
        "portal",
        "auth_signup",
    ],
    "data": [
        "data/ir_config_parameter_data.xml",
        "views/homepage_templates.xml",
    ],
    "installable": True,
    "application": False,
}
