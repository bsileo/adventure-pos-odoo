# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.service_date_utils import INTERVAL_UNITS, compute_schedule_dates


class AdventureEquipmentServiceOverrideWizard(models.TransientModel):
    _name = "adventure.equipment.service.override.wizard"
    _description = "Override Equipment Service Schedule"

    requirement_id = fields.Many2one(
        "adventure.equipment.service.requirement",
        required=True,
        ondelete="cascade",
    )
    next_due_date = fields.Date(required=True)
    warning_date = fields.Date()
    interval_quantity = fields.Integer()
    interval_unit = fields.Selection(INTERVAL_UNITS)
    is_recurring = fields.Boolean()
    reason = fields.Text(required=True)
    expiration_date = fields.Date(string="Override Expiration")

    @api.onchange("requirement_id")
    def _onchange_requirement_id(self):
        if not self.requirement_id:
            return
        self.next_due_date = self.requirement_id.next_due_date
        self.warning_date = self.requirement_id.warning_date
        self.interval_quantity = self.requirement_id.interval_quantity
        self.interval_unit = self.requirement_id.interval_unit
        self.is_recurring = self.requirement_id.is_recurring

    def action_apply(self):
        self.ensure_one()
        if not self.env.user.has_group("adventure_equipment.group_equipment_manager"):
            raise UserError(_("Only equipment managers may override schedules."))
        warning_date = self.warning_date
        grace_date = self.requirement_id.grace_date
        if self.next_due_date and not warning_date:
            warning_date, _, grace_date = compute_schedule_dates(
                self.next_due_date,
                warning_lead_days=self.requirement_id.warning_lead_days,
                grace_days=self.requirement_id.grace_days,
            )
        self.requirement_id.write(
            {
                "override_active": True,
                "override_next_due_date": self.next_due_date,
                "override_warning_date": warning_date,
                "override_interval_quantity": self.interval_quantity,
                "override_interval_unit": self.interval_unit,
                "override_is_recurring": self.is_recurring,
                "override_reason": self.reason,
                "override_user_id": self.env.user.id,
                "override_date": fields.Datetime.now(),
                "override_expiration_date": self.expiration_date,
                "next_due_date": self.next_due_date,
                "warning_date": warning_date,
                "grace_date": grace_date,
                "schedule_source": "override",
                "next_recommended_from_record": False,
            }
        )
        self.requirement_id._recompute_status()
        return {"type": "ir.actions.act_window_close"}
