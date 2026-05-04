# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureRentalAsset(models.Model):
    _name = "adventure.rental.asset"
    _description = "Rental Asset"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one("product.product", required=True)
    lot_id = fields.Many2one("stock.lot", string="Serial/Lot")
    barcode = fields.Char()
    state = fields.Selection(
        [
            ("available", "Available"),
            ("reserved", "Reserved"),
            ("checked_out", "Checked Out"),
            ("maintenance_due", "Maintenance Due"),
            ("repair", "Repair"),
            ("retired", "Retired"),
        ],
        default="available",
        required=True,
    )
    condition_state = fields.Selection(
        [
            ("good", "Good"),
            ("worn", "Worn"),
            ("damaged", "Damaged"),
            ("missing", "Missing"),
        ],
        default="good",
        required=True,
    )
    service_due_date = fields.Date()
    current_reservation_line_id = fields.Many2one("adventure.rental.line")
    requirement_payload = fields.Json(default=dict)
