# -*- coding: utf-8 -*-
{
    "name": "Adventure Product Category",
    "summary": "Extended product categories with canonical name, aliases, keywords, and level.",
    "version": "18.0.1.0.1",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["product", "stock"],
    "external_dependencies": {
        "python": ["rapidfuzz"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/product_category_views.xml",
        "views/vendor_catalog_import_views.xml",
    ],
    "installable": True,
    "application": True,
}
