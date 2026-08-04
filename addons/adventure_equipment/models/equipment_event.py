# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AdventureEquipmentEvent(models.Model):
    _name = "adventure.equipment.event"
    _description = "Equipment Event"
    _order = "event_date desc, id desc"

    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        string="Equipment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    event_date = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    event_type = fields.Selection(
        [
            ("registered", "Registered"),
            ("product_linked", "Product Linked"),
            ("product_refreshed", "Product Refreshed"),
            ("serial_corrected", "Serial Corrected"),
            ("ownership_transferred", "Ownership Transferred"),
            ("condition_updated", "Condition Updated"),
            ("lifecycle_changed", "Lifecycle Changed"),
            ("retired", "Retired"),
            ("reactivated", "Reactivated"),
            ("document_added", "Document Added"),
            ("imported", "Imported"),
        ],
        string="Event Type",
        required=True,
        index=True,
    )
    summary = fields.Text(required=True)
    payload = fields.Json(default=dict)
    user_id = fields.Many2one(
        "res.users",
        string="User",
        default=lambda self: self.env.uid,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )

    def write(self, vals):
        if not self.env.context.get("equipment_allow_event_write"):
            raise UserError(_("Equipment events are read-only and cannot be modified."))
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get("equipment_allow_event_write"):
            raise UserError(_("Equipment events are read-only and cannot be deleted."))
        return super().unlink()
