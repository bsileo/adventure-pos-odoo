# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    smartwaiver_waiver_ids = fields.One2many(
        "smartwaiver.waiver",
        "partner_id",
        string="Smartwaiver waivers",
    )
    smartwaiver_waiver_count = fields.Integer(
        string="Waiver count",
        compute="_compute_smartwaiver_stats",
    )
    smartwaiver_status = fields.Selection(
        [
            ("none", "None"),
            ("valid", "Valid"),
            ("expired", "Expired only"),
        ],
        string="Smartwaiver status",
        compute="_compute_smartwaiver_stats",
    )

    @api.depends(
        "smartwaiver_waiver_ids",
        "smartwaiver_waiver_ids.expired",
        "smartwaiver_waiver_ids.expiration_date",
    )
    def _compute_smartwaiver_stats(self):
        today = fields.Date.context_today(self)
        for partner in self:
            waivers = partner.smartwaiver_waiver_ids
            partner.smartwaiver_waiver_count = len(waivers)
            if not waivers:
                partner.smartwaiver_status = "none"
                continue
            has_valid = False
            for waiver in waivers:
                if waiver.expired:
                    continue
                if waiver.expiration_date and waiver.expiration_date < today:
                    continue
                has_valid = True
                break
            partner.smartwaiver_status = "valid" if has_valid else "expired"

    def action_view_smartwaiver_waivers(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Smartwaiver waivers"),
            "res_model": "smartwaiver.waiver",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    def action_search_smartwaiver(self):
        self.ensure_one()
        Waiver = self.env["smartwaiver.waiver"]
        if not Waiver._get_api_key():
            raise UserError(
                _(
                    "Configure a Smartwaiver API key in Settings or "
                    "SMARTWAIVER_API_KEY before searching."
                )
            )
        imported = Waiver.search_and_import_for_partner(self)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Smartwaiver"),
                "message": _("Imported or refreshed %s waiver(s).") % len(imported),
                "type": "success",
                "sticky": False,
                "next": self.action_view_smartwaiver_waivers(),
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        Waiver = self.env["smartwaiver.waiver"]
        for partner in partners:
            if partner.email:
                Waiver.rematch_unmatched_for_email(partner.email)
        return partners

    def write(self, vals):
        emails_before = {p.id: p.email for p in self}
        result = super().write(vals)
        if "email" in vals:
            Waiver = self.env["smartwaiver.waiver"]
            for partner in self:
                if partner.email and partner.email != emails_before.get(partner.id):
                    Waiver.rematch_unmatched_for_email(partner.email)
                elif partner.email:
                    Waiver.rematch_unmatched_for_email(partner.email)
        return result
