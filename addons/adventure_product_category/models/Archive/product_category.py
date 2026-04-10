# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    canonical_name = fields.Char(
        string="Canonical name",
        help="Stable label for integrations (e.g. normalized or external system name).",
        index="btree_not_null",
    )
    alias_names = fields.Json(
        string="Alias names",
        help='Alternate display or match names as a JSON list of strings, e.g. ["First stage", "1st stage"].',
        default=list,
    )
    keywords = fields.Json(
        string="Keywords",
        help="Search or matching keywords as a JSON list of strings.",
        default=list,
    )
    category_level = fields.Selection(
        selection=[
            ("l1", "L1"),
            ("l2", "L2"),
            ("l3", "L3"),
            ("l4", "L4"),
        ],
        string="Category level",
        help="Optional tier in your taxonomy. The tree is still defined by Parent Category (parent_id).",
    )
