# -*- coding: utf-8 -*-

from odoo import _, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    def action_adventure_pos_add_category_tree_to_pos(self):
        """Enable POS for all products in this category and its children."""
        Product = self.env["product.template"]
        all_templates = Product.search([("categ_id", "child_of", self.ids)])
        all_templates._adventure_pos_enable_templates()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Point of Sale"),
                "message": _(
                    "%s product(s) under the selected categories (including subcategories) are now "
                    "available in the POS.",
                    len(all_templates),
                ),
                "type": "success",
                "sticky": False,
            },
        }
