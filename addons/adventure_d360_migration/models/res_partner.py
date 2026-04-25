# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    d360_customer_id = fields.Char(copy=False, index=True)
    d360_external_ref = fields.Char(copy=False)
    d360_partner_kind = fields.Selection(
        [
            ("person", "Person"),
            ("company", "Company"),
            ("ambiguous", "Ambiguous"),
        ],
        copy=False,
    )
    d360_customer_type = fields.Char(copy=False)
    d360_invoice_type = fields.Char(copy=False)
    d360_last_purchase_date = fields.Date(copy=False)
    d360_birthday = fields.Date(copy=False)
    d360_last_import_batch_id = fields.Many2one(
        "adventure.d360.customer.import.batch",
        copy=False,
    )
