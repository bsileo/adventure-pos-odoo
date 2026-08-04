# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    equipment_asset_ids = fields.One2many(
        "adventure.equipment.asset",
        "partner_id",
        string="Owned Equipment",
    )
    equipment_asset_count = fields.Integer(
        string="Equipment Count",
        compute="_compute_equipment_asset_count",
    )

    @api.depends("equipment_asset_ids")
    def _compute_equipment_asset_count(self):
        """Count assets where this partner is the direct current owner.

        This is contact-only ownership (``partner_id`` on the asset), not
        commercial aggregation across child contacts or companies.
        """
        if not self.ids:
            for partner in self:
                partner.equipment_asset_count = 0
            return

        Asset = self.env["adventure.equipment.asset"]
        grouped = Asset.read_group(
            [("partner_id", "in", self.ids)],
            ["partner_id"],
            ["partner_id"],
        )
        count_by_partner = {
            row["partner_id"][0]: row["partner_id_count"]
            for row in grouped
            if row.get("partner_id")
        }
        for partner in self:
            partner.equipment_asset_count = count_by_partner.get(partner.id, 0)

    def action_view_equipment_assets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Equipment"),
            "res_model": "adventure.equipment.asset",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
