# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    history_archive_order_ids = fields.One2many(
        "adventure.history.order",
        "partner_id",
        string="D360 historical archive orders",
    )
    history_archive_order_count = fields.Integer(
        string="D360 archive order count",
        compute="_compute_history_archive_order_count",
    )

    @api.depends("history_archive_order_ids")
    def _compute_history_archive_order_count(self):
        for partner in self:
            partner.history_archive_order_count = len(partner.history_archive_order_ids)

    def action_view_history_archive_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Historical archive orders"),
            "res_model": "adventure.history.order",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

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
