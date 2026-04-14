# -*- coding: utf-8 -*-

from odoo import _, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_adventure_pos_add_vendor_catalog_to_pos(self):
        """Enable POS for every product that lists this partner (or children) as vendor."""
        SupplierInfo = self.env["product.supplierinfo"]
        roots = self.mapped("commercial_partner_id")
        suppliers = SupplierInfo.search([("partner_id", "child_of", roots.ids)])
        templates = suppliers.product_tmpl_id
        templates._adventure_pos_enable_templates()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Point of Sale"),
                "message": _(
                    "%s product(s) from this vendor’s catalog are now available in the POS.",
                    len(templates),
                ),
                "type": "success",
                "sticky": False,
            },
        }
