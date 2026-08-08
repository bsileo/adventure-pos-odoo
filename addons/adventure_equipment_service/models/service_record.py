# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .service_date_utils import add_interval, compute_schedule_dates, to_date


class AdventureEquipmentServiceRecord(models.Model):
    _name = "adventure.equipment.service.record"
    _description = "Equipment Service Record"
    _order = "service_date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, copy=False, default=lambda self: _("New"))
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        string="Equipment",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        related="asset_id.partner_id",
        store=True,
        index=True,
    )
    service_type_id = fields.Many2one(
        "adventure.equipment.service.type",
        string="Service Type",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    requirement_id = fields.Many2one(
        "adventure.equipment.service.requirement",
        string="Satisfied Requirement",
        ondelete="set null",
        index=True,
        tracking=True,
    )
    service_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("completed", "Completed"),
            ("verified", "Verified"),
            ("voided", "Voided"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    verification_state = fields.Selection(
        [
            ("unverified", "Unverified"),
            ("pending", "Pending"),
            ("verified", "Verified"),
            ("disputed", "Disputed"),
        ],
        default="unverified",
        required=True,
        tracking=True,
    )

    performed_by_this_shop = fields.Boolean(
        string="Performed by Current Shop",
        default=True,
        tracking=True,
    )
    provider_partner_id = fields.Many2one(
        "res.partner",
        string="Service Provider",
        ondelete="restrict",
    )
    external_provider_name = fields.Char()
    technician_user_id = fields.Many2one("res.users", string="Technician")
    external_technician_name = fields.Char()

    summary = fields.Char()
    findings = fields.Text()
    work_performed = fields.Text()
    recommendations = fields.Text()
    condition_before = fields.Selection(
        related="asset_id.condition_state",
        string="Condition Before (asset)",
        readonly=True,
    )
    condition_before_manual = fields.Char(string="Condition Before")
    condition_after = fields.Char(string="Condition After")
    result = fields.Selection(
        [
            ("passed", "Passed"),
            ("failed", "Failed"),
            ("completed", "Completed"),
            ("incomplete", "Incomplete"),
            ("advisory", "Advisory"),
            ("not_applicable", "Not Applicable"),
        ],
        tracking=True,
    )
    usage_meter_value = fields.Float(string="Usage / Meter Value")
    customer_visible_report = fields.Html(
        string="Customer-Visible Report",
    )
    internal_notes = fields.Text(
        groups="adventure_equipment.group_equipment_user",
    )

    certificate_number = fields.Char(string="Certificate / Reference")
    certificate_issuer = fields.Char()
    certificate_issue_date = fields.Date()
    certificate_expiration_date = fields.Date()

    next_recommended_date = fields.Date(
        string="Next Recommended Service Date",
        tracking=True,
        help="When set on completion, takes precedence over policy interval calculation.",
    )
    source_record_ref = fields.Char()
    external_reference = fields.Char()
    data_provenance = fields.Selection(
        [
            ("shop", "Shop"),
            ("external", "External Provider"),
            ("customer_reported", "Customer Reported"),
            ("imported", "Imported"),
            ("other", "Other"),
        ],
        default="shop",
        required=True,
    )
    imported = fields.Boolean()
    customer_reported = fields.Boolean()

    void_reason = fields.Text()
    void_user_id = fields.Many2one("res.users")
    void_date = fields.Datetime()

    attachment_count = fields.Integer(compute="_compute_attachment_count")

    @api.depends("asset_id")
    def _compute_attachment_count(self):
        Attachment = self.env["ir.attachment"]
        for row in self:
            row.attachment_count = Attachment.search_count(
                [("res_model", "=", self._name), ("res_id", "=", row.id)]
            )

    @api.constrains("asset_id", "company_id")
    def _check_company_consistency(self):
        for row in self:
            if row.asset_id and row.company_id and row.asset_id.company_id != row.company_id:
                raise ValidationError(
                    _("Service record company must match the equipment company.")
                )
            if (
                row.requirement_id
                and row.requirement_id.asset_id
                and row.requirement_id.asset_id != row.asset_id
            ):
                raise ValidationError(
                    _("Service requirement must belong to the same equipment asset.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", _("New")) in (_("New"), "New"):
                company = vals.get("company_id") or self.env.company.id
                vals["name"] = (
                    sequence.with_company(company).next_by_code(
                        "adventure.equipment.service.record"
                    )
                    or _("New")
                )
            if vals.get("customer_reported"):
                vals.setdefault("data_provenance", "customer_reported")
                vals.setdefault("performed_by_this_shop", False)
            if vals.get("performed_by_this_shop") is False and not vals.get(
                "data_provenance"
            ):
                vals["data_provenance"] = "external"
        return super().create(vals_list)

    def write(self, vals):
        protected = self.filtered(lambda row: row.state in ("completed", "verified", "voided"))
        if protected and not self.env.context.get("equipment_service_force_write"):
            allowed = {
                "state",
                "verification_state",
                "void_reason",
                "void_user_id",
                "void_date",
                "message_main_attachment_id",
            }
            # Managers may still update verification annotations lightly.
            if not set(vals).issubset(allowed):
                if any(row.state == "voided" for row in protected):
                    raise UserError(_("Voided service records cannot be modified."))
                if any(row.state == "verified" for row in protected):
                    raise UserError(
                        _(
                            "Verified service records are protected. Void the record "
                            "and create a corrected replacement instead."
                        )
                    )
                if any(row.state == "completed" for row in protected) and not self.env.user.has_group(
                    "adventure_equipment.group_equipment_manager"
                ):
                    raise UserError(
                        _("Only equipment managers can alter completed service records.")
                    )
        return super().write(vals)

    def unlink(self):
        if any(row.state != "draft" for row in self):
            raise UserError(
                _("Only draft service records can be deleted. Void completed records instead.")
            )
        return super().unlink()

    def action_complete(self):
        for row in self:
            if row.state != "draft":
                raise UserError(_("Only draft service records can be completed."))
            if row.service_type_id.requires_result and not row.result:
                raise UserError(_("This service type requires a result before completion."))
            if row.service_type_id.requires_certificate and not row.certificate_number:
                raise UserError(
                    _("This service type requires a certificate/reference before completion.")
                )
            row.write({"state": "completed"})
            row._apply_to_requirement()
        return True

    def action_verify(self):
        for row in self:
            if row.state not in ("completed", "verified"):
                raise UserError(_("Only completed service records can be verified."))
            row.with_context(equipment_service_force_write=True).write(
                {"state": "verified", "verification_state": "verified"}
            )
        return True

    def action_void(self):
        for row in self:
            if row.state == "draft":
                raise UserError(_("Delete draft records instead of voiding them."))
            if not row.void_reason:
                raise UserError(_("A void reason is required."))
            row.with_context(equipment_service_force_write=True).write(
                {
                    "state": "voided",
                    "void_user_id": self.env.user.id,
                    "void_date": fields.Datetime.now(),
                }
            )
        return True

    def _find_matching_requirement(self):
        """Deterministic requirement match for completion.

        Prefer explicit ``requirement_id``. Otherwise choose the single active
        policy-managed or open requirement for the same asset + service type,
        preferring non-completed recurring requirements.
        """
        self.ensure_one()
        if self.requirement_id:
            return self.requirement_id
        Requirement = self.env["adventure.equipment.service.requirement"]
        domain = [
            ("asset_id", "=", self.asset_id.id),
            ("service_type_id", "=", self.service_type_id.id),
            ("active", "=", True),
            ("status", "!=", "completed"),
        ]
        candidates = Requirement.search(domain, order="is_policy_managed desc, id asc")
        if len(candidates) == 1:
            return candidates
        # Prefer policy-managed recurring requirement.
        policy_managed = candidates.filtered("is_policy_managed")
        if len(policy_managed) == 1:
            return policy_managed
        return candidates[:1]

    def _apply_to_requirement(self):
        """Update matched requirement after completion.

        Next-due precedence:
        1. Explicit ``next_recommended_date`` on this record
        2. Active asset-specific override (left intact; due not overwritten)
        3. Matching service policy interval from service_date
        4. Unknown (clear due only if no basis)
        """
        for row in self:
            requirement = row._find_matching_requirement()
            if not requirement:
                row.asset_id._recompute_service_rollup()
                continue
            vals = {
                "last_completed_date": row.service_date,
                "last_service_record_id": row.id,
                "forecast_confidence": "confirmed"
                if row.verification_state == "verified" or row.performed_by_this_shop
                else "customer_reported"
                if row.customer_reported
                else "estimated",
            }
            if requirement.is_one_time:
                vals.update(
                    {
                        "status": "completed",
                        "next_due_date": False,
                        "warning_date": False,
                        "grace_date": False,
                    }
                )
                requirement.write(vals)
                requirement.asset_id._recompute_service_rollup()
                continue

            if requirement.override_active:
                vals["schedule_source"] = "override"
                requirement.write(vals)
                requirement._recompute_status()
                requirement.asset_id._recompute_service_rollup()
                continue

            if row.next_recommended_date:
                warning_date, due_date, grace_date = compute_schedule_dates(
                    row.next_recommended_date,
                    warning_lead_days=requirement.warning_lead_days,
                    grace_days=requirement.grace_days,
                )
                vals.update(
                    {
                        "next_due_date": due_date,
                        "warning_date": warning_date,
                        "grace_date": grace_date,
                        "baseline_date": row.service_date,
                        "next_recommended_from_record": True,
                        "schedule_source": "service_record",
                    }
                )
            elif requirement.source_policy_id and requirement.is_recurring:
                due = add_interval(
                    row.service_date,
                    requirement.interval_quantity or requirement.source_policy_id.interval_quantity,
                    requirement.interval_unit or requirement.source_policy_id.interval_unit,
                )
                warning_date, due_date, grace_date = compute_schedule_dates(
                    due,
                    warning_lead_days=requirement.warning_lead_days,
                    grace_days=requirement.grace_days,
                )
                vals.update(
                    {
                        "next_due_date": due_date,
                        "warning_date": warning_date,
                        "grace_date": grace_date,
                        "baseline_date": row.service_date,
                        "next_recommended_from_record": False,
                        "schedule_source": "policy",
                    }
                )
            elif requirement.is_recurring and requirement.interval_quantity and requirement.interval_unit:
                due = add_interval(
                    row.service_date,
                    requirement.interval_quantity,
                    requirement.interval_unit,
                )
                warning_date, due_date, grace_date = compute_schedule_dates(
                    due,
                    warning_lead_days=requirement.warning_lead_days,
                    grace_days=requirement.grace_days,
                )
                vals.update(
                    {
                        "next_due_date": due_date,
                        "warning_date": warning_date,
                        "grace_date": grace_date,
                        "baseline_date": row.service_date,
                        "schedule_source": "manual",
                    }
                )
            else:
                vals.update(
                    {
                        "next_due_date": False,
                        "warning_date": False,
                        "grace_date": False,
                        "forecast_confidence": "incomplete_history",
                    }
                )

            requirement.write(vals)
            if "status" not in vals:
                requirement._recompute_status()
            if not row.requirement_id:
                row.with_context(equipment_service_force_write=True).write(
                    {"requirement_id": requirement.id}
                )
            requirement.asset_id._recompute_service_rollup()
