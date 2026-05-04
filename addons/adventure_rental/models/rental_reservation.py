# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureRentalReservation(models.Model):
    _name = "adventure.rental.reservation"
    _description = "Rental Reservation"
    _order = "pickup_datetime desc, id desc"

    name = fields.Char(default="New", required=True)
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    pickup_datetime = fields.Datetime(required=True)
    return_datetime = fields.Datetime(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("reserved", "Reserved"),
            ("assigned", "Assigned"),
            ("checked_out", "Checked Out"),
            ("returned", "Returned"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
    )
    line_ids = fields.One2many("adventure.rental.line", "reservation_id", string="Rental Lines")
    sale_order_id = fields.Many2one("sale.order", string="Sales Order")
    pos_order_id = fields.Many2one("pos.order", string="POS Order")
    deposit_amount = fields.Monetary(currency_field="currency_id")
    fee_amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    requirement_payload = fields.Json(default=dict)

    def _validation_result(self, code, severity, message, record=None, payload=None):
        return {
            "code": code,
            "severity": severity,
            "message": message,
            "record_model": record._name if record else False,
            "record_id": record.id if record else False,
            "payload": payload or {},
        }

    def _get_customer_requirement_results(self):
        return []

    def _get_reservation_validation_results(self):
        return []

    def _get_checkout_validation_results(self):
        return []

    def _get_return_inspection_results(self):
        return []

    def _get_fee_line_candidates(self):
        return []

    def _get_post_return_routes(self):
        return []

    def _get_receipt_metadata(self):
        return {}
