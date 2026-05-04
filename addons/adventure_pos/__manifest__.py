# -*- coding: utf-8 -*-
{
    "name": "Adventure POS",
    "summary": "Retail POS extensions for Adventure POS (MVP scaffold).",
    "version": "19.0.1.0.2",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_base", "contacts", "product", "point_of_sale", "sale", "stock"],
    "data": [
        "data/product_category_data.xml",
        "data/pos_category_data.xml",
        "views/views.xml",
        "views/templates.xml",
        "views/pos_catalog_views.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "adventure_pos/static/src/pos/js/mode_registry.js",
            "adventure_pos/static/src/pos/js/adventure_pos_shell.js",
            "adventure_pos/static/src/pos/xml/adventure_pos_shell.xml",
            "adventure_pos/static/src/pos/scss/adventure_pos.scss",
        ],
    },
    "installable": True,
    "application": True,
}
