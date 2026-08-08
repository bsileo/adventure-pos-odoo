# -*- coding: utf-8 -*-

from odoo.addons.adventure_ai.services.capability_registry import (
    Capability,
    register_capability,
)


SEARCH_PRODUCTS_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Natural-language or keyword product search text from the cashier.",
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of products to return (1-50).",
        },
        "available_in_pos_only": {
            "type": "boolean",
            "description": "If true, only return products available in POS.",
        },
        "category_name": {
            "type": "string",
            "description": "Optional product category name filter.",
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}


def _search_products_handler(env, args, context):
    return env["adventure.product_search"].search_products(
        query=args.get("query"),
        limit=args.get("limit", 12),
        available_in_pos_only=args.get("available_in_pos_only", True),
        category_name=args.get("category_name") or None,
    )


register_capability(
    Capability(
        name="search_products",
        description=(
            "Search sellable products by natural language or keywords "
            "(name, internal reference, barcode, category). Read-only."
        ),
        parameters=SEARCH_PRODUCTS_PARAMETERS,
        handler=_search_products_handler,
        risk_class="read",
        feature="pos_retail",
        profiles=("pos_retail", "default"),
        group_xmlids=("adventure_ai.group_user",),
        execution_mode="read",
    )
)
