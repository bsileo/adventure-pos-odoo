# -*- coding: utf-8 -*-
{
    "name": "Adventure POS",
    "summary": "Retail POS extensions for Adventure POS (MVP scaffold).",
    "version": "1.0.0",
    "category": "Point of Sale",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_base", "product", "point_of_sale"],
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
    "installable": True,
}
