# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureRentalLine(models.Model):
    _name = "adventure.rental.line"
    _description = "Rental Line"

    reservation_id = fields.Many2one(
        "adventure.rental.reservation",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one("product.product", required=True)
    package_template_id = fields.Many2one("adventure.rental.package.template")
    asset_id = fields.Many2one("adventure.rental.asset")
    quantity = fields.Float(default=1.0, required=True)
    price_unit = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(related="reservation_id.currency_id", store=True)
    size_code = fields.Char()
    condition_state = fields.Selection(
        [
            ("ready", "Ready"),
            ("checked_out", "Checked Out"),
            ("returned", "Returned"),
            ("maintenance_due", "Maintenance Due"),
            ("damaged", "Damaged"),
        ],
        default="ready",
    )
    requirement_payload = fields.Json(default=dict)
