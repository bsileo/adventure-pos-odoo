# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureRentalMaintenanceEvent(models.Model):
    _name = "adventure.rental.maintenance.event"
    _description = "Rental Maintenance Event"
    _order = "event_date desc, id desc"

    asset_id = fields.Many2one("adventure.rental.asset", required=True, ondelete="cascade")
    event_date = fields.Date(default=fields.Date.context_today, required=True)
    event_type = fields.Selection(
        [
            ("service", "Service"),
            ("hold", "Hold"),
            ("repair", "Repair"),
            ("inspection", "Inspection"),
            ("retirement", "Retirement"),
        ],
        required=True,
    )
    state = fields.Selection(
        [
            ("open", "Open"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="open",
        required=True,
    )
    notes = fields.Text()
    next_service_date = fields.Date()
    payload = fields.Json(default=dict)
