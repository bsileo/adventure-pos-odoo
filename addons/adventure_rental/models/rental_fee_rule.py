# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureRentalFeeRule(models.Model):
    _name = "adventure.rental.fee.rule"
    _description = "Rental Fee Rule"
    _order = "sequence, name"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    fee_type = fields.Selection(
        [
            ("deposit", "Deposit"),
            ("late", "Late"),
            ("damage", "Damage"),
            ("adjustment", "Adjustment"),
        ],
        required=True,
    )
    amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    product_id = fields.Many2one("product.product", string="Fee Product")
    payload = fields.Json(default=dict)
