# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AdventureEquipmentServiceCompleteWizard(models.TransientModel):
    _name = "adventure.equipment.service.complete.wizard"
    _description = "Record Equipment Service"

    requirement_id = fields.Many2one(
        "adventure.equipment.service.requirement",
        ondelete="cascade",
    )
    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        required=True,
        ondelete="cascade",
    )
    service_type_id = fields.Many2one(
        "adventure.equipment.service.type",
        required=True,
        ondelete="cascade",
    )
    service_date = fields.Date(required=True, default=fields.Date.context_today)
    performed_by_this_shop = fields.Boolean(default=True)
    provider_partner_id = fields.Many2one("res.partner")
    external_provider_name = fields.Char()
    technician_user_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
    )
    result = fields.Selection(
        [
            ("passed", "Passed"),
            ("failed", "Failed"),
            ("completed", "Completed"),
            ("incomplete", "Incomplete"),
            ("advisory", "Advisory"),
            ("not_applicable", "Not Applicable"),
        ],
        default="passed",
    )
    summary = fields.Char()
    findings = fields.Text()
    work_performed = fields.Text()
    certificate_number = fields.Char()
    next_recommended_date = fields.Date()
    verification_state = fields.Selection(
        [
            ("unverified", "Unverified"),
            ("pending", "Pending"),
            ("verified", "Verified"),
            ("disputed", "Disputed"),
        ],
        default="unverified",
    )
    complete_immediately = fields.Boolean(default=True)

    @api.onchange("requirement_id")
    def _onchange_requirement_id(self):
        if self.requirement_id:
            self.asset_id = self.requirement_id.asset_id
            self.service_type_id = self.requirement_id.service_type_id

    def action_confirm(self):
        self.ensure_one()
        if not self.env.user.has_group("adventure_equipment.group_equipment_user"):
            raise UserError(_("You are not allowed to record equipment service."))
        values = {
            "asset_id": self.asset_id.id,
            "company_id": self.asset_id.company_id.id,
            "service_type_id": self.service_type_id.id,
            "requirement_id": self.requirement_id.id,
            "service_date": self.service_date,
            "performed_by_this_shop": self.performed_by_this_shop,
            "provider_partner_id": self.provider_partner_id.id,
            "external_provider_name": self.external_provider_name,
            "technician_user_id": self.technician_user_id.id,
            "result": self.result,
            "summary": self.summary or self.service_type_id.name,
            "findings": self.findings,
            "work_performed": self.work_performed,
            "certificate_number": self.certificate_number,
            "next_recommended_date": self.next_recommended_date,
            "verification_state": self.verification_state,
            "data_provenance": "shop" if self.performed_by_this_shop else "external",
        }
        record = self.env["adventure.equipment.service.record"].create(values)
        if self.complete_immediately:
            record.action_complete()
        return {
            "type": "ir.actions.act_window",
            "res_model": "adventure.equipment.service.record",
            "res_id": record.id,
            "view_mode": "form",
            "target": "current",
        }
