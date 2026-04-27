# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureHistoryOrderLine(models.Model):
    _name = "adventure.history.order.line"
    _description = "Historical sales order line (archive)"
    _order = "order_id, line_sequence, id"

    order_id = fields.Many2one(
        "adventure.history.order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    line_sequence = fields.Integer(string="Seq.", required=True, default=1)

    d360_line_xmlid = fields.Char(
        string="Line idempotency key",
        required=True,
        index=True,
        copy=False,
        help="d360.history_order_line.{Location}.{Invoice number}.{line_sequence} (sanitized).",
    )

    part_number = fields.Char(index=True)
    barcode = fields.Char(index=True)
    description = fields.Text()
    serial_number = fields.Char()
    category = fields.Char()
    vendor = fields.Char()
    department = fields.Char()
    manufacturer = fields.Char()
    taxable = fields.Boolean()
    tax_collected_1 = fields.Float()
    tax_collected_2 = fields.Float()
    tax_collected_3 = fields.Float()

    sold_qty = fields.Float()
    unit_price = fields.Float()
    extended_price = fields.Float()
    delivered_qty = fields.Float()
    returned_qty = fields.Float()
    date_delivered = fields.Datetime()
    cost = fields.Float()
    extended_cost = fields.Float()
    margin = fields.Float()

    technician = fields.Char()
    instructor = fields.Char()
    primary_color = fields.Char()
    secondary_color = fields.Char()
    accent_color = fields.Char()
    size = fields.Char()

    product_id = fields.Many2one("product.product", string="Matched product", index=True)
    product_match_status = fields.Selection(
        [
            ("unmatched", "Unmatched"),
            ("barcode", "Barcode"),
            ("default_code", "Part number / SKU"),
            ("composite", "Part + vendor / mfr + description"),
            ("ambiguous", "Ambiguous"),
        ],
        string="Product match",
        default="unmatched",
        index=True,
    )
    product_match_notes = fields.Text()

    is_duplicate_candidate = fields.Boolean(
        string="Duplicate candidate",
        help="Exact duplicate of another row in the same source file (same invoice).",
    )
    is_negative_qty = fields.Boolean(
        string="Negative / return line",
        help="Sold Qty is negative or Returned Qty is non-zero.",
    )

    # Denormalized for search from order list (related stored)
    order_invoice_number = fields.Char(
        related="order_id.invoice_number",
        store=True,
        index=True,
        readonly=True,
    )
    order_partner_id = fields.Many2one(
        related="order_id.partner_id",
        store=True,
        index=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "adventure_history_order_line_d360_xmlid_uniq",
            "unique(d360_line_xmlid)",
            "An archive line with this idempotency key already exists.",
        ),
        (
            "adventure_history_order_line_order_seq_uniq",
            "unique(order_id, line_sequence)",
            "Line sequence must be unique per order.",
        ),
    ]
