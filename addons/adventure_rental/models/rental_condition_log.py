# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureRentalConditionLog(models.Model):
    _name = "adventure.rental.condition.log"
    _description = "Rental Condition Log"
    _order = "create_date desc, id desc"

    reservation_id = fields.Many2one("adventure.rental.reservation", ondelete="cascade")
    line_id = fields.Many2one("adventure.rental.line", ondelete="cascade")
    asset_id = fields.Many2one("adventure.rental.asset", required=True)
    event_type = fields.Selection(
        [
            ("checkout", "Checkout"),
            ("checkin", "Check-In"),
            ("inspection", "Inspection"),
        ],
        required=True,
    )
    condition_state = fields.Selection(
        [
            ("good", "Good"),
            ("worn", "Worn"),
            ("damaged", "Damaged"),
            ("missing", "Missing"),
        ],
        required=True,
    )
    notes = fields.Text()
    payload = fields.Json(default=dict)
