# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class AdventureEquipmentServiceWaiverWizard(models.TransientModel):
    _name = "adventure.equipment.service.waiver.wizard"
    _description = "Waive or Suspend Equipment Service Requirement"

    requirement_id = fields.Many2one(
        "adventure.equipment.service.requirement",
        required=True,
        ondelete="cascade",
    )
    action = fields.Selection(
        [
            ("waive", "Waive"),
            ("suspend", "Suspend"),
            ("not_applicable", "Mark Not Applicable"),
            ("restore", "Restore"),
        ],
        required=True,
        default="waive",
    )
    reason = fields.Text()
    expiration_date = fields.Date(
        string="Expiration",
        help="When set for waive, the requirement returns to evaluation after this date.",
    )

    def action_confirm(self):
        self.ensure_one()
        if not self.env.user.has_group("adventure_equipment.group_equipment_manager"):
            raise UserError(_("Only equipment managers may waive or suspend requirements."))
        req = self.requirement_id
        if self.action == "restore":
            req.action_restore_evaluation()
            return {"type": "ir.actions.act_window_close"}
        if self.action != "restore" and not self.reason:
            raise UserError(_("A reason is required."))
        vals = {}
        if self.action == "waive":
            vals = {
                "waived": True,
                "suspended": False,
                "not_applicable": False,
                "waiver_reason": self.reason,
                "waiver_user_id": self.env.user.id,
                "waiver_date": fields.Datetime.now(),
                "waiver_expiration_date": self.expiration_date,
            }
        elif self.action == "suspend":
            vals = {
                "suspended": True,
                "waived": False,
                "not_applicable": False,
                "suspend_reason": self.reason,
            }
        elif self.action == "not_applicable":
            vals = {
                "not_applicable": True,
                "waived": False,
                "suspended": False,
                "suspend_reason": self.reason,
            }
        req.write(vals)
        req._recompute_status()
        return {"type": "ir.actions.act_window_close"}
