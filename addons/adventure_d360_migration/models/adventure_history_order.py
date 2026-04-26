# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AdventureHistoryOrder(models.Model):
    _name = "adventure.history.order"
    _description = "Non-posting historical sales order (archive)"
    _order = "invoice_date desc, id desc"

    name = fields.Char(string="Reference", required=True, index=True)
    d360_source_xmlid = fields.Char(
        string="Idempotency key",
        required=True,
        index=True,
        copy=False,
        help="Stable key: d360.history_order.{Location}.{Invoice number} (sanitized).",
    )
    source_system = fields.Char(
        default="D360",
        required=True,
        help="Source system label for this archive row.",
    )
    location = fields.Char(index=True)
    invoice_type = fields.Char()
    invoice_number = fields.Char(string="Invoice number", index=True)
    invoice_date = fields.Datetime(index=True)
    sales_person = fields.Char()

    d360_customer_id = fields.Char(string="D360 Customer ID", index=True)
    partner_id = fields.Many2one("res.partner", string="Matched customer", index=True)
    customer_match_status = fields.Selection(
        [
            ("unmatched", "Unmatched"),
            ("d360_id", "D360 Customer ID"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("name_address", "Name + address"),
            ("ambiguous", "Ambiguous"),
        ],
        string="Customer match",
        default="unmatched",
        index=True,
    )
    customer_match_notes = fields.Text()

    snapshot_first_name = fields.Char()
    snapshot_last_name = fields.Char()
    snapshot_email = fields.Char(index=True)
    snapshot_phone = fields.Char()
    snapshot_address_1 = fields.Char()
    snapshot_address_2 = fields.Char()
    snapshot_city = fields.Char()
    snapshot_state = fields.Char()
    snapshot_zip = fields.Char()
    snapshot_country = fields.Char()
    snapshot_customer_type = fields.Char()

    import_batch_id = fields.Many2one(
        "adventure.d360.history.import.batch",
        string="Import batch",
        ondelete="set null",
    )

    line_ids = fields.One2many(
        "adventure.history.order.line",
        "order_id",
        string="Lines",
    )
    line_count = fields.Integer(compute="_compute_line_stats", store=True)
    unmatched_product_lines = fields.Integer(compute="_compute_line_stats", store=True)

    @api.depends("line_ids", "line_ids.product_match_status")
    def _compute_line_stats(self):
        for order in self:
            lines = order.line_ids
            order.line_count = len(lines)
            order.unmatched_product_lines = sum(
                1 for line in lines if line.product_match_status == "unmatched"
            )

    _sql_constraints = [
        (
            "adventure_history_order_d360_xmlid_uniq",
            "unique(d360_source_xmlid)",
            "An archive order with this idempotency key already exists.",
        ),
    ]
