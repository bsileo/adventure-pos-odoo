# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    adventure_waiver_ids = fields.One2many(
        "adventure.waiver",
        "partner_id",
        string="Waivers",
    )
    adventure_waiver_count = fields.Integer(
        string="Waiver count",
        compute="_compute_adventure_waiver_stats",
    )
    adventure_waiver_status = fields.Selection(
        [
            ("none", "None"),
            ("valid", "Valid"),
            ("expired", "Expired only"),
        ],
        string="Waiver status",
        compute="_compute_adventure_waiver_stats",
    )

    @api.depends(
        "adventure_waiver_ids",
        "adventure_waiver_ids.expired",
        "adventure_waiver_ids.expiration_date",
    )
    def _compute_adventure_waiver_stats(self):
        today = fields.Date.context_today(self)
        for partner in self:
            waivers = partner.adventure_waiver_ids
            partner.adventure_waiver_count = len(waivers)
            if not waivers:
                partner.adventure_waiver_status = "none"
                continue
            has_valid = False
            for waiver in waivers:
                if waiver.expired:
                    continue
                if waiver.expiration_date and waiver.expiration_date < today:
                    continue
                has_valid = True
                break
            partner.adventure_waiver_status = "valid" if has_valid else "expired"

    def action_view_adventure_waivers(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Waivers"),
            "res_model": "adventure.waiver",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    def action_search_provider_waivers(self):
        """Ask installed provider connectors to search/import waivers for this partner."""
        self.ensure_one()
        imported = self.env["adventure.waiver"]._provider_search_and_import_for_partner(
            self
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Waivers"),
                "message": _("Imported or refreshed %s waiver(s).") % len(imported),
                "type": "success",
                "sticky": False,
                "next": self.action_view_adventure_waivers(),
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        Waiver = self.env["adventure.waiver"]
        for partner in partners:
            if partner.email:
                Waiver.rematch_unmatched_for_email(partner.email)
        return partners

    def write(self, vals):
        result = super().write(vals)
        if "email" in vals:
            Waiver = self.env["adventure.waiver"]
            for partner in self:
                if partner.email:
                    Waiver.rematch_unmatched_for_email(partner.email)
        return result
