# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .service_date_utils import (
    INTERVAL_UNITS,
    SERVICE_CRON_BATCH_SIZE,
    add_interval,
    compute_requirement_status,
    compute_schedule_dates,
    to_date,
)


class AdventureEquipmentServiceRequirement(models.Model):
    _name = "adventure.equipment.service.requirement"
    _description = "Equipment Service Requirement"
    _order = "next_due_date asc nulls last, id desc"
    _inherit = ["mail.thread"]
    _rec_name = "display_name"

    name = fields.Char(required=True, tracking=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)
    active = fields.Boolean(default=True)
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
        ondelete="cascade",
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
    source_policy_id = fields.Many2one(
        "adventure.equipment.service.policy",
        string="Source Policy",
        ondelete="set null",
        index=True,
        tracking=True,
    )
    source_classification = fields.Selection(
        [
            ("policy", "Policy"),
            ("manual", "Manual"),
            ("bulletin", "Bulletin"),
            ("other", "Other"),
        ],
        default="policy",
        required=True,
        tracking=True,
    )
    is_manual = fields.Boolean(
        compute="_compute_is_manual",
        store=True,
    )
    is_policy_managed = fields.Boolean(
        string="Policy Managed",
        default=True,
        help="When set, sync may update schedule from the winning policy.",
    )

    # Scheduling
    baseline_date = fields.Date(tracking=True)
    last_completed_date = fields.Date(tracking=True)
    next_due_date = fields.Date(tracking=True, index=True)
    warning_date = fields.Date(index=True)
    grace_date = fields.Date(index=True)
    interval_quantity = fields.Integer()
    interval_unit = fields.Selection(INTERVAL_UNITS)
    is_recurring = fields.Boolean(default=True, tracking=True)
    is_one_time = fields.Boolean(default=False, tracking=True)

    warning_lead_days = fields.Integer(default=30)
    grace_days = fields.Integer(default=0)

    status = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("current", "Current"),
            ("due_soon", "Due Soon"),
            ("due", "Due"),
            ("overdue", "Overdue"),
            ("waived", "Waived"),
            ("suspended", "Suspended"),
            ("not_applicable", "Not Applicable"),
            ("completed", "Completed"),
        ],
        default="unknown",
        required=True,
        index=True,
        tracking=True,
        copy=False,
    )
    days_until_due = fields.Integer(compute="_compute_days_until_due")

    forecast_confidence = fields.Selection(
        [
            ("confirmed", "Confirmed"),
            ("estimated", "Estimated"),
            ("customer_reported", "Customer Reported"),
            ("imported", "Imported"),
            ("incomplete_history", "Incomplete History"),
            ("unknown", "Unknown"),
        ],
        default="estimated",
        required=True,
        tracking=True,
    )

    # Manual provenance
    manual_reason = fields.Text()
    severity = fields.Selection(
        [
            ("info", "Info"),
            ("normal", "Normal"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        default="normal",
    )
    customer_explanation = fields.Text()
    internal_notes = fields.Text(
        groups="adventure_equipment.group_equipment_user",
    )
    created_by_user_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        readonly=True,
    )

    # Overrides
    override_active = fields.Boolean(tracking=True)
    override_next_due_date = fields.Date(tracking=True)
    override_warning_date = fields.Date()
    override_interval_quantity = fields.Integer()
    override_interval_unit = fields.Selection(INTERVAL_UNITS)
    override_is_recurring = fields.Boolean()
    override_reason = fields.Text(tracking=True)
    override_user_id = fields.Many2one("res.users", tracking=True)
    override_date = fields.Datetime(tracking=True)
    override_expiration_date = fields.Date(tracking=True)
    schedule_source = fields.Selection(
        [
            ("policy", "Policy"),
            ("override", "Override"),
            ("service_record", "Service Record Recommendation"),
            ("manual", "Manual"),
        ],
        default="policy",
        tracking=True,
    )

    # Waiver / suspension
    waived = fields.Boolean(tracking=True)
    waiver_reason = fields.Text(tracking=True)
    waiver_user_id = fields.Many2one("res.users", tracking=True)
    waiver_date = fields.Datetime(tracking=True)
    waiver_expiration_date = fields.Date(tracking=True)
    suspended = fields.Boolean(tracking=True)
    suspend_reason = fields.Text(tracking=True)
    not_applicable = fields.Boolean(tracking=True)

    next_recommended_from_record = fields.Boolean(
        string="Next Due From Service Record",
        help="Set when an explicit next recommended date from a service record is in effect.",
    )
    last_service_record_id = fields.Many2one(
        "adventure.equipment.service.record",
        string="Last Service Record",
        ondelete="set null",
    )

    @api.depends("name", "asset_id", "service_type_id")
    def _compute_display_name(self):
        for row in self:
            parts = []
            if row.asset_id:
                parts.append(row.asset_id.name)
            if row.service_type_id:
                parts.append(row.service_type_id.name)
            elif row.name:
                parts.append(row.name)
            row.display_name = " — ".join(parts) if parts else row.name or _("Requirement")

    @api.depends("source_classification", "source_policy_id")
    def _compute_is_manual(self):
        for row in self:
            row.is_manual = row.source_classification == "manual" or not row.source_policy_id

    @api.depends("next_due_date")
    def _compute_days_until_due(self):
        today = fields.Date.context_today(self)
        for row in self:
            if not row.next_due_date:
                row.days_until_due = 0
            else:
                row.days_until_due = (row.next_due_date - today).days

    @api.constrains("asset_id", "company_id")
    def _check_company_consistency(self):
        for row in self:
            if row.asset_id and row.company_id and row.asset_id.company_id != row.company_id:
                raise ValidationError(
                    _("Service requirement company must match the equipment company.")
                )

    @api.onchange("is_one_time")
    def _onchange_is_one_time(self):
        if self.is_one_time:
            self.is_recurring = False

    def _policy_schedule_values(self, policy, asset, last_completed=None, today=None):
        today = to_date(today) or fields.Date.context_today(self)
        last_completed = to_date(last_completed)
        baseline = last_completed
        if not baseline:
            if policy.first_due_basis == "acquired_on":
                baseline = asset.acquired_on
            elif policy.first_due_basis == "ownership_start":
                baseline = asset.ownership_start_date
            elif policy.first_due_basis == "today":
                baseline = today
            else:
                baseline = asset.in_service_date or asset.ownership_start_date or today
        baseline = to_date(baseline) or today

        if policy.is_recurring:
            due = add_interval(baseline, policy.interval_quantity, policy.interval_unit)
        else:
            due = baseline

        warning_date, due_date, grace_date = compute_schedule_dates(
            due,
            warning_lead_days=policy.warning_lead_days,
            grace_days=policy.grace_days,
        )
        return {
            "baseline_date": baseline,
            "next_due_date": due_date,
            "warning_date": warning_date,
            "grace_date": grace_date,
            "interval_quantity": policy.interval_quantity if policy.is_recurring else 0,
            "interval_unit": policy.interval_unit if policy.is_recurring else False,
            "is_recurring": policy.is_recurring,
            "is_one_time": not policy.is_recurring,
            "warning_lead_days": policy.warning_lead_days,
            "grace_days": policy.grace_days,
            "schedule_source": "policy",
        }

    def _apply_override_to_values(self, values):
        self.ensure_one()
        if not self.override_active:
            return values
        if self.override_expiration_date and self.override_expiration_date < fields.Date.context_today(self):
            return values
        if self.override_next_due_date:
            values["next_due_date"] = self.override_next_due_date
        if self.override_warning_date:
            values["warning_date"] = self.override_warning_date
        elif values.get("next_due_date"):
            warning_date, due_date, grace_date = compute_schedule_dates(
                values["next_due_date"],
                warning_lead_days=self.override_interval_quantity
                and self.warning_lead_days
                or self.warning_lead_days,
                grace_days=self.grace_days,
            )
            if self.override_next_due_date:
                warning_date, due_date, grace_date = compute_schedule_dates(
                    self.override_next_due_date,
                    warning_lead_days=self.warning_lead_days,
                    grace_days=self.grace_days,
                )
                values["warning_date"] = warning_date
                values["grace_date"] = grace_date
        if self.override_interval_quantity:
            values["interval_quantity"] = self.override_interval_quantity
        if self.override_interval_unit:
            values["interval_unit"] = self.override_interval_unit
        if self.override_is_recurring is not None and self.override_active:
            # Only apply when explicitly set on the override wizard path.
            pass
        values["schedule_source"] = "override"
        return values

    def _recompute_status(self, today=None):
        today = to_date(today) or fields.Date.context_today(self)
        for row in self:
            status = compute_requirement_status(
                today=today,
                due_date=row.next_due_date,
                warning_date=row.warning_date,
                grace_date=row.grace_date,
                waived=row.waived,
                suspended=row.suspended,
                not_applicable=row.not_applicable,
                completed=row.status == "completed" and row.is_one_time,
            )
            # Preserve completed one-time unless explicitly restored.
            if row.is_one_time and row.status == "completed" and not row.waived and not row.suspended:
                status = "completed"
            if row.status != status:
                # Skip chatter tracking noise for routine aging.
                row.with_context(mail_notrack=True).write({"status": status})

    def action_recalculate_status(self):
        self._recompute_status()
        return True

    def action_restore_policy_schedule(self):
        for row in self:
            if not row.source_policy_id:
                raise UserError(_("This requirement has no source policy to restore."))
            vals = {
                "override_active": False,
                "override_next_due_date": False,
                "override_warning_date": False,
                "override_interval_quantity": 0,
                "override_interval_unit": False,
                "override_reason": False,
                "override_user_id": False,
                "override_date": False,
                "override_expiration_date": False,
                "next_recommended_from_record": False,
                "schedule_source": "policy",
            }
            schedule = row._policy_schedule_values(
                row.source_policy_id,
                row.asset_id,
                last_completed=row.last_completed_date,
            )
            vals.update(schedule)
            row.write(vals)
            row._recompute_status()
        return True

    def action_open_override_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Override Schedule"),
            "res_model": "adventure.equipment.service.override.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_requirement_id": self.id},
        }

    def action_open_waiver_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Waive / Suspend Requirement"),
            "res_model": "adventure.equipment.service.waiver.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_requirement_id": self.id},
        }

    def action_open_complete_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Record Service"),
            "res_model": "adventure.equipment.service.complete.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_requirement_id": self.id,
                "default_asset_id": self.asset_id.id,
                "default_service_type_id": self.service_type_id.id,
            },
        }

    def action_restore_evaluation(self):
        self.write(
            {
                "waived": False,
                "waiver_reason": False,
                "waiver_user_id": False,
                "waiver_date": False,
                "waiver_expiration_date": False,
                "suspended": False,
                "suspend_reason": False,
                "not_applicable": False,
            }
        )
        self._recompute_status()
        return True

    def _expire_temporary_states(self, today=None):
        today = to_date(today) or fields.Date.context_today(self)
        for row in self:
            vals = {}
            if row.waived and row.waiver_expiration_date and row.waiver_expiration_date < today:
                vals.update(
                    {
                        "waived": False,
                        "waiver_reason": False,
                        "waiver_user_id": False,
                        "waiver_date": False,
                        "waiver_expiration_date": False,
                    }
                )
            if (
                row.override_active
                and row.override_expiration_date
                and row.override_expiration_date < today
            ):
                vals.update(
                    {
                        "override_active": False,
                        "schedule_source": "policy" if row.source_policy_id else "manual",
                    }
                )
                if row.source_policy_id:
                    schedule = row._policy_schedule_values(
                        row.source_policy_id,
                        row.asset_id,
                        last_completed=row.last_completed_date,
                        today=today,
                    )
                    vals.update(schedule)
            if vals:
                row.write(vals)

    @api.model
    def sync_asset_requirements(self, assets, on_date=None):
        """Create/update/deactivate policy-managed requirements for assets.

        Deduplication strategy:
        * At most one **policy-managed** active requirement per
          (asset, service_type).
        * Manual / bulletin requirements are never removed by sync.
        * Competing policies for the same service type collapse to the
          winning policy; the requirement's ``source_policy_id`` is updated.
        """
        Policy = self.env["adventure.equipment.service.policy"]
        on_date = to_date(on_date) or fields.Date.context_today(self)
        for asset in assets:
            winners = Policy.select_winning_policies(asset, on_date=on_date)
            winner_by_type = {policy.service_type_id.id: policy for policy in winners}
            existing = self.search(
                [
                    ("asset_id", "=", asset.id),
                    ("is_policy_managed", "=", True),
                    ("active", "=", True),
                ]
            )
            existing_by_type = {}
            for req in existing:
                existing_by_type.setdefault(req.service_type_id.id, self.browse())
                existing_by_type[req.service_type_id.id] |= req

            keep_ids = self.browse()
            for type_id, policy in winner_by_type.items():
                reqs = existing_by_type.get(type_id, self.browse())
                req = reqs[:1]
                extras = reqs[1:]
                if extras:
                    extras.write({"active": False, "suspended": True, "suspend_reason": _("Superseded duplicate")})
                schedule = self._prepare_policy_schedule(
                    policy,
                    asset,
                    last_completed=req.last_completed_date if req else None,
                    today=on_date,
                )
                values = {
                    "name": _("%(type)s for %(asset)s")
                    % {"type": policy.service_type_id.name, "asset": asset.name},
                    "asset_id": asset.id,
                    "company_id": asset.company_id.id,
                    "service_type_id": policy.service_type_id.id,
                    "source_policy_id": policy.id,
                    "source_classification": "policy",
                    "is_policy_managed": True,
                    "forecast_confidence": "estimated"
                    if not (req and req.last_completed_date)
                    else "confirmed",
                    **schedule,
                }
                if req:
                    if req.override_active and not (
                        req.override_expiration_date and req.override_expiration_date < on_date
                    ):
                        # Preserve override dates; still refresh policy link/meta.
                        values = {
                            "source_policy_id": policy.id,
                            "name": values["name"],
                            "interval_quantity": values["interval_quantity"]
                            if not req.override_interval_quantity
                            else req.interval_quantity,
                            "interval_unit": values["interval_unit"]
                            if not req.override_interval_unit
                            else req.interval_unit,
                            "warning_lead_days": policy.warning_lead_days,
                            "grace_days": policy.grace_days,
                            "is_recurring": policy.is_recurring
                            if not req.override_active
                            else req.is_recurring,
                        }
                        # Keep current next_due when override active.
                    elif req.next_recommended_from_record and req.next_due_date:
                        values = {
                            "source_policy_id": policy.id,
                            "name": values["name"],
                            "interval_quantity": schedule["interval_quantity"],
                            "interval_unit": schedule["interval_unit"],
                            "warning_lead_days": policy.warning_lead_days,
                            "grace_days": policy.grace_days,
                            "is_recurring": schedule["is_recurring"],
                            "is_one_time": schedule["is_one_time"],
                            "schedule_source": "service_record",
                        }
                    req.write(values)
                    keep_ids |= req
                else:
                    keep_ids |= self.create(values)

            obsolete = existing - keep_ids
            if obsolete:
                obsolete.write(
                    {
                        "active": False,
                        "suspended": True,
                        "suspend_reason": _("No longer matched by an active policy"),
                    }
                )

            (keep_ids | existing)._expire_temporary_states(today=on_date)
            (keep_ids | existing)._recompute_status(today=on_date)
            asset._recompute_service_rollup()
        return True

    @api.model
    def _prepare_policy_schedule(self, policy, asset, last_completed=None, today=None):
        """Build schedule values from a policy without requiring a requirement row."""
        today = to_date(today) or fields.Date.context_today(self)
        last_completed = to_date(last_completed)
        baseline = last_completed
        if not baseline:
            if policy.first_due_basis == "acquired_on":
                baseline = asset.acquired_on
            elif policy.first_due_basis == "ownership_start":
                baseline = asset.ownership_start_date
            elif policy.first_due_basis == "today":
                baseline = today
            else:
                baseline = asset.in_service_date or asset.ownership_start_date or today
        baseline = to_date(baseline) or today
        if policy.is_recurring:
            due = add_interval(baseline, policy.interval_quantity, policy.interval_unit)
        else:
            due = baseline
        warning_date, due_date, grace_date = compute_schedule_dates(
            due,
            warning_lead_days=policy.warning_lead_days,
            grace_days=policy.grace_days,
        )
        return {
            "baseline_date": baseline,
            "next_due_date": due_date,
            "warning_date": warning_date,
            "grace_date": grace_date,
            "interval_quantity": policy.interval_quantity if policy.is_recurring else 0,
            "interval_unit": policy.interval_unit if policy.is_recurring else False,
            "is_recurring": policy.is_recurring,
            "is_one_time": not policy.is_recurring,
            "warning_lead_days": policy.warning_lead_days,
            "grace_days": policy.grace_days,
            "schedule_source": "policy",
        }

    @api.model
    def cron_process_equipment_service(self, batch_size=None):
        """Idempotent scheduled processor.

        Responsibilities:
        * Expire waivers/overrides
        * Age requirement statuses
        * Sync policies for a bounded asset batch
        * Recompute asset rollups

        Continuation: processes assets with ``id > last_id`` stored in
        ``ir.config_parameter``, wrapping to the start when exhausted.
        """
        batch_size = int(batch_size or SERVICE_CRON_BATCH_SIZE)
        ICP = self.env["ir.config_parameter"].sudo()
        param_key = "adventure_equipment_service.cron_last_asset_id"
        last_id = int(ICP.get_param(param_key, "0") or 0)
        Asset = self.env["adventure.equipment.asset"]
        assets = Asset.search(
            [("active", "=", True), ("id", ">", last_id)],
            order="id",
            limit=batch_size,
        )
        if not assets and last_id:
            assets = Asset.search([("active", "=", True)], order="id", limit=batch_size)
            last_id = 0
        if assets:
            self.sync_asset_requirements(assets)
            # Also age any requirements not touched via sync (manual).
            manual = self.search(
                [
                    ("asset_id", "in", assets.ids),
                    ("is_policy_managed", "=", False),
                    ("active", "=", True),
                ]
            )
            manual._expire_temporary_states()
            manual._recompute_status()
            assets._recompute_service_rollup()
            ICP.set_param(param_key, str(assets[-1].id))
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("is_one_time"):
                vals["is_recurring"] = False
            if vals.get("source_classification") == "manual":
                vals.setdefault("is_policy_managed", False)
                vals.setdefault("schedule_source", "manual")
            if vals.get("next_due_date") and not vals.get("warning_date"):
                warning_date, due_date, grace_date = compute_schedule_dates(
                    vals["next_due_date"],
                    warning_lead_days=vals.get("warning_lead_days", 30),
                    grace_days=vals.get("grace_days", 0),
                )
                vals["warning_date"] = warning_date
                vals["grace_date"] = grace_date
        records = super().create(vals_list)
        records._recompute_status()
        records.mapped("asset_id")._recompute_service_rollup()
        return records

    def write(self, vals):
        if vals.get("is_one_time"):
            vals["is_recurring"] = False
        res = super().write(vals)
        status_triggers = {
            "next_due_date",
            "warning_date",
            "grace_date",
            "waived",
            "suspended",
            "not_applicable",
            "override_active",
            "active",
        }
        if status_triggers.intersection(vals):
            if "next_due_date" in vals and "warning_date" not in vals:
                for row in self:
                    warning_date, due_date, grace_date = compute_schedule_dates(
                        row.next_due_date,
                        warning_lead_days=row.warning_lead_days,
                        grace_days=row.grace_days,
                    )
                    super(AdventureEquipmentServiceRequirement, row).write(
                        {"warning_date": warning_date, "grace_date": grace_date}
                    )
            self._recompute_status()
            self.mapped("asset_id")._recompute_service_rollup()
        return res
