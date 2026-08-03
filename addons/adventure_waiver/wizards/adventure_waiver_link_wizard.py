# -*- coding: utf-8 -*-

from odoo import _, fields, models


class AdventureWaiverLinkWizard(models.TransientModel):
    _name = "adventure.waiver.link.wizard"
    _description = "Link waiver to customer"

    waiver_id = fields.Many2one(
        "adventure.waiver",
        required=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
    )

    def action_link(self):
        self.ensure_one()
        self.waiver_id.write(
            {
                "partner_id": self.partner_id.id,
                "match_state": "manual",
                "match_method": "manual",
                "match_notes": _("Linked manually"),
            }
        )
        return {"type": "ir.actions.act_window_close"}
