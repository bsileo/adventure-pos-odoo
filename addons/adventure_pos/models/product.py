# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_rental = fields.Boolean(string="Is rental", default=False)

    pos_vendor_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="product_tmpl_pos_vendor_partner_rel",
        column1="product_tmpl_id",
        column2="partner_id",
        string="Vendors (POS filter)",
        compute="_compute_pos_vendor_partner_ids",
        store=True,
        help="Commercial vendors from purchase tab; used to filter products for POS catalog setup.",
    )

    @api.depends("seller_ids.partner_id")
    def _compute_pos_vendor_partner_ids(self):
        for tmpl in self:
            tmpl.pos_vendor_partner_ids = tmpl.seller_ids.partner_id

    def _adventure_pos_enable_templates(self):
        """Enable POS + sales and sync POS categories from inventory category names."""
        if not self:
            return
        self.write({"sale_ok": True, "available_in_pos": True})
        self._sync_pos_category_from_inventory_category()

    def action_adventure_pos_add_to_pos(self):
        """Add selected rows to POS, or if none selected, every product matching current list filters."""
        Product = self.env["product.template"]
        if self:
            products = self
        else:
            domain = list(self.env.context.get("active_domain") or [])
            if not domain:
                raise UserError(
                    _(
                        "Select one or more products, or clear the selection and narrow the list with "
                        "filters or search (category sidebar, vendor sidebar, or search bar). "
                        "Adding the entire catalog without filters is blocked."
                    )
                )
            products = Product.search(domain)
            if not products:
                raise UserError(_("No products match the current filters."))
        products._adventure_pos_enable_templates()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Point of Sale"),
                "message": _("%s product(s) are now available in the POS.", len(products)),
                "type": "success",
                "sticky": False,
            },
        }

    def _sync_pos_category_from_inventory_category(self):
        """Set POS category to match inventory category by name (fallback to Misc)."""
        PosCategory = self.env["pos.category"]
        misc = PosCategory.search([("name", "=", "Misc")], limit=1)

        for product in self:
            name = product.categ_id.name if product.categ_id else False
            if not name:
                # No inventory category -> keep existing POS categories
                continue

            pos_cat = PosCategory.search([("name", "=", name)], limit=1)
            if pos_cat:
                product.pos_categ_ids = [(6, 0, pos_cat.ids)]
            elif misc:
                product.pos_categ_ids = [(6, 0, misc.ids)]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Sync after create so `categ_id` is available on record
        records._sync_pos_category_from_inventory_category()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "categ_id" in vals:
            self._sync_pos_category_from_inventory_category()
        return res
