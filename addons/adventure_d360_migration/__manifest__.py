# -*- coding: utf-8 -*-
{
    "name": "Adventure D360 Migration",
    "summary": "Dive Shop 360 migration workflow scaffolding for Adventure POS.",
    "version": "18.0.1.0.4",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_base", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "views/d360_customer_import_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "adventure_d360_migration/static/src/js/d360_partner_kind_actions.js",
        ],
    },
    "installable": True,
    "application": True,
}
