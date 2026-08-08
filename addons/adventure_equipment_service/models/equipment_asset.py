# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

from .service_date_utils import rollup_asset_service_status


class AdventureEquipmentAsset(models.Model):
    _inherit = "adventure.equipment.asset"

    service_requirement_ids = fields.One2many(
        "adventure.equipment.service.requirement",
        "asset_id",
        string="Service Requirements",
    )
    service_record_ids = fields.One2many(
        "adventure.equipment.service.record",
        "asset_id",
        string="Service History",
    )
    service_status = fields.Selection(
        [
            ("not_applicable", "Not Applicable"),
            ("unknown", "Unknown"),
            ("current", "Current"),
            ("due_soon", "Due Soon"),
            ("due", "Due"),
            ("overdue", "Overdue"),
            ("attention_required", "Attention Required"),
        ],
        default="not_applicable",
        compute="_compute_service_rollup",
        store=True,
        index=True,
    )
    next_service_due_date = fields.Date(
        compute="_compute_service_rollup",
        store=True,
        index=True,
    )
    service_requirement_count = fields.Integer(
        compute="_compute_service_rollup",
        store=True,
    )
    service_due_soon_count = fields.Integer(
        compute="_compute_service_rollup",
        store=True,
    )
    service_due_count = fields.Integer(
        compute="_compute_service_rollup",
        store=True,
    )
    service_overdue_count = fields.Integer(
        compute="_compute_service_rollup",
        store=True,
    )
    service_unknown_count = fields.Integer(
        compute="_compute_service_rollup",
        store=True,
    )
    service_record_count = fields.Integer(
        compute="_compute_service_rollup",
        store=True,
    )

    @api.depends(
        "service_requirement_ids",
        "service_requirement_ids.status",
        "service_requirement_ids.next_due_date",
        "service_requirement_ids.active",
        "service_record_ids",
        "service_record_ids.state",
    )
    def _compute_service_rollup(self):
        for asset in self:
            requirements = asset.service_requirement_ids.filtered("active")
            records = asset.service_record_ids.filtered(
                lambda row: row.state in ("completed", "verified")
            )
            statuses = requirements.mapped("status")
            asset.service_status = rollup_asset_service_status(statuses)
            open_reqs = requirements.filtered(
                lambda row: row.status
                not in ("waived", "suspended", "completed", "not_applicable")
                and row.next_due_date
            )
            asset.next_service_due_date = (
                min(open_reqs.mapped("next_due_date")) if open_reqs else False
            )
            asset.service_requirement_count = len(requirements)
            asset.service_due_soon_count = len(
                requirements.filtered(lambda row: row.status == "due_soon")
            )
            asset.service_due_count = len(
                requirements.filtered(lambda row: row.status == "due")
            )
            asset.service_overdue_count = len(
                requirements.filtered(lambda row: row.status == "overdue")
            )
            asset.service_unknown_count = len(
                requirements.filtered(lambda row: row.status == "unknown")
            )
            asset.service_record_count = len(records)

    def _recompute_service_rollup(self):
        self._compute_service_rollup()

    def action_recalculate_service_requirements(self):
        Requirement = self.env["adventure.equipment.service.requirement"]
        Requirement.sync_asset_requirements(self)
        return True

    def action_view_service_requirements(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Service Requirements"),
            "res_model": "adventure.equipment.service.requirement",
            "view_mode": "list,form",
            "domain": [("asset_id", "=", self.id)],
            "context": {
                "default_asset_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }

    def action_view_service_records(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Service History"),
            "res_model": "adventure.equipment.service.record",
            "view_mode": "list,form",
            "domain": [("asset_id", "=", self.id)],
            "context": {
                "default_asset_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }
