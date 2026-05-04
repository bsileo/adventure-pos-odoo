# -*- coding: utf-8 -*-
{
    "name": "Adventure Rental",
    "summary": "Generic rental reservations, assets, pickup, and return workflows.",
    "version": "19.0.1.0.0",
    "category": "Adventure POS",
    "author": "Adventure POS",
    "license": "LGPL-3",
    "depends": ["adventure_pos", "stock"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "adventure_rental/static/src/pos/js/rental_data.js",
            "adventure_rental/static/src/pos/js/rental_popup.js",
            "adventure_rental/static/src/pos/js/rental_screens.js",
            "adventure_rental/static/src/pos/js/modes/rental_mode.js",
            "adventure_rental/static/src/pos/js/modes/rental_modes.js",
            "adventure_rental/static/src/pos/js/product_screen_patch.js",
            "adventure_rental/static/src/pos/xml/modes/rental_mode.xml",
            "adventure_rental/static/src/pos/xml/rental_popup.xml",
            "adventure_rental/static/src/pos/xml/rental_screens.xml",
            "adventure_rental/static/src/pos/scss/rental_pos.scss",
        ],
    },
    "installable": True,
    "application": True,
}
