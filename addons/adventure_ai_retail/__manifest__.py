# -*- coding: utf-8 -*-
{
    "name": "Adventure AI Retail",
    "summary": "Retail AI capabilities: product search and POS natural-language search panel.",
    "version": "19.0.1.0.0",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_ai", "adventure_pos", "point_of_sale", "product"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "adventure_ai_retail/static/src/pos/js/ai_search_panel.js",
            "adventure_ai_retail/static/src/pos/js/navbar_ai_button.js",
            "adventure_ai_retail/static/src/pos/xml/ai_search_panel.xml",
            "adventure_ai_retail/static/src/pos/xml/navbar_ai_button.xml",
            "adventure_ai_retail/static/src/pos/scss/ai_retail_pos.scss",
        ],
    },
    "installable": True,
    "application": False,
}
