# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    equipment_service_due_soon_count = fields.Integer(
        compute="_compute_equipment_service_summary",
        store=True,
        string="Equipment Due Soon",
    )
    equipment_service_due_count = fields.Integer(
        compute="_compute_equipment_service_summary",
        store=True,
        string="Equipment Due",
    )
    equipment_service_overdue_count = fields.Integer(
        compute="_compute_equipment_service_summary",
        store=True,
        string="Equipment Overdue",
    )
    equipment_next_service_due_date = fields.Date(
        compute="_compute_equipment_service_summary",
        store=True,
        string="Next Equipment Service",
    )

    @api.depends(
        "equipment_asset_ids.service_due_soon_count",
        "equipment_asset_ids.service_due_count",
        "equipment_asset_ids.service_overdue_count",
        "equipment_asset_ids.next_service_due_date",
    )
    def _compute_equipment_service_summary(self):
        """Contact-only ownership rollup (no commercial parent aggregation)."""
        for partner in self:
            assets = partner.equipment_asset_ids
            partner.equipment_service_due_soon_count = sum(
                assets.mapped("service_due_soon_count")
            )
            partner.equipment_service_due_count = sum(assets.mapped("service_due_count"))
            partner.equipment_service_overdue_count = sum(
                assets.mapped("service_overdue_count")
            )
            dates = [d for d in assets.mapped("next_service_due_date") if d]
            partner.equipment_next_service_due_date = min(dates) if dates else False

    def action_view_equipment_service_requirements(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Equipment Service"),
            "res_model": "adventure.equipment.service.requirement",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
