# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .service_date_utils import INTERVAL_UNITS, to_date


class AdventureEquipmentServicePolicy(models.Model):
    _name = "adventure.equipment.service.policy"
    _description = "Equipment Service Policy"
    _order = "sequence, name, id"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10)
    description = fields.Text()

    service_type_id = fields.Many2one(
        "adventure.equipment.service.type",
        string="Service Type",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    policy_source = fields.Selection(
        [
            ("manufacturer", "Manufacturer"),
            ("regulatory", "Regulatory"),
            ("shop", "Shop"),
            ("internal", "Internal Standard"),
            ("customer_agreement", "Customer Agreement"),
            ("other", "Other"),
        ],
        default="shop",
        required=True,
        tracking=True,
    )
    priority = fields.Integer(
        default=10,
        help="Higher priority wins when specificity scores are equal.",
        tracking=True,
    )
    date_effective = fields.Date(string="Effective Date", tracking=True)
    date_expiration = fields.Date(string="Expiration Date", tracking=True)

    # Applicability (structured matching — no stored expressions)
    category_id = fields.Many2one(
        "adventure.equipment.category",
        string="Equipment Category",
        ondelete="cascade",
        index=True,
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product Template",
        ondelete="cascade",
        index=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product Variant",
        ondelete="cascade",
        index=True,
    )
    tag_id = fields.Many2one(
        "adventure.equipment.tag",
        string="Equipment Tag",
        ondelete="cascade",
        index=True,
    )
    brand_name = fields.Char(index=True)
    manufacturer_name = fields.Char(index=True)
    model_name = fields.Char(index=True)
    is_default = fields.Boolean(
        string="Company Default Rule",
        help="Matches all equipment in the company when no more specific rule applies.",
        tracking=True,
    )

    # Schedule
    is_recurring = fields.Boolean(default=True, tracking=True)
    interval_quantity = fields.Integer(default=12, tracking=True)
    interval_unit = fields.Selection(
        INTERVAL_UNITS,
        default="months",
        tracking=True,
    )
    warning_lead_days = fields.Integer(
        string="Warning Lead Days",
        default=30,
        tracking=True,
    )
    grace_days = fields.Integer(string="Grace Days", default=0, tracking=True)
    first_due_basis = fields.Selection(
        [
            ("in_service_date", "In-Service Date"),
            ("acquired_on", "Acquired Date"),
            ("ownership_start", "Ownership Start"),
            ("today", "Activation / Today"),
        ],
        string="First Due Basis",
        default="in_service_date",
        required=True,
        tracking=True,
    )
    auto_generate_requirements = fields.Boolean(
        string="Automatic Requirement Generation",
        default=True,
        tracking=True,
    )

    requirement_ids = fields.One2many(
        "adventure.equipment.service.requirement",
        "source_policy_id",
        string="Requirements",
    )

    @api.constrains("date_effective", "date_expiration")
    def _check_effective_dates(self):
        for policy in self:
            if (
                policy.date_effective
                and policy.date_expiration
                and policy.date_expiration < policy.date_effective
            ):
                raise ValidationError(
                    _("Policy expiration date cannot be before the effective date.")
                )

    @api.constrains("interval_quantity", "is_recurring")
    def _check_interval(self):
        for policy in self:
            if policy.is_recurring and policy.interval_quantity <= 0:
                raise ValidationError(
                    _("Recurring policies require a positive interval quantity.")
                )

    @api.onchange("service_type_id")
    def _onchange_service_type_id(self):
        if not self.service_type_id:
            return
        self.warning_lead_days = self.service_type_id.default_warning_lead_days
        self.grace_days = self.service_type_id.default_grace_days
        if not self.service_type_id.supports_recurring:
            self.is_recurring = False

    def _is_effective_on(self, on_date=None):
        self.ensure_one()
        on_date = to_date(on_date) or fields.Date.context_today(self)
        if not self.active:
            return False
        if self.date_effective and on_date < self.date_effective:
            return False
        if self.date_expiration and on_date > self.date_expiration:
            return False
        return True

    def _specificity_score(self):
        """Deterministic specificity for precedence (higher wins)."""
        self.ensure_one()
        if self.product_id:
            return 100
        if self.product_tmpl_id:
            return 90
        if self.brand_name and self.model_name:
            return 80
        if self.brand_name or self.manufacturer_name or self.model_name:
            return 70
        if self.category_id:
            return 60
        if self.tag_id:
            return 50
        if self.is_default:
            return 10
        # Untargeted non-default policies are weakest company-wide matchers.
        return 5

    def _matches_asset(self, asset, on_date=None):
        self.ensure_one()
        if not self._is_effective_on(on_date):
            return False
        if self.company_id and asset.company_id != self.company_id:
            return False
        if self.product_id and asset.product_id != self.product_id:
            return False
        if self.product_tmpl_id and asset.product_tmpl_id != self.product_tmpl_id:
            return False
        if self.category_id and asset.category_id != self.category_id:
            return False
        if self.tag_id and self.tag_id not in asset.tag_ids:
            return False
        if self.brand_name and (asset.brand_name or "").strip().lower() != self.brand_name.strip().lower():
            return False
        if self.manufacturer_name and (
            asset.manufacturer_name or ""
        ).strip().lower() != self.manufacturer_name.strip().lower():
            return False
        if self.model_name and (asset.model_name or "").strip().lower() != self.model_name.strip().lower():
            return False
        # Default / untargeted policies match when no targeting fields fail.
        return True

    @api.model
    def find_applicable_policies(self, asset, on_date=None):
        """Return active policies that match ``asset`` on ``on_date``."""
        on_date = to_date(on_date) or fields.Date.context_today(self)
        domain = [
            ("active", "=", True),
            ("auto_generate_requirements", "=", True),
            ("company_id", "=", asset.company_id.id),
            "|",
            ("date_effective", "=", False),
            ("date_effective", "<=", on_date),
            "|",
            ("date_expiration", "=", False),
            ("date_expiration", ">=", on_date),
        ]
        candidates = self.search(domain)
        return candidates.filtered(lambda policy: policy._matches_asset(asset, on_date))

    @api.model
    def select_winning_policies(self, asset, on_date=None):
        """Resolve precedence: one winning policy per service type.

        Precedence within a service type (highest wins):
        1. Product variant
        2. Product template
        3. Brand + model (then brand/manufacturer/model alone)
        4. Category
        5. Tag
        6. Company default / untargeted

        Tie-breakers: higher ``priority``, then lower ``id``.
        Different service types remain independent.
        """
        applicable = self.find_applicable_policies(asset, on_date=on_date)
        winners = {}
        for policy in applicable:
            key = policy.service_type_id.id
            current = winners.get(key)
            if not current:
                winners[key] = policy
                continue
            score = policy._specificity_score()
            current_score = current._specificity_score()
            if score > current_score:
                winners[key] = policy
            elif score == current_score and (
                policy.priority > current.priority
                or (policy.priority == current.priority and policy.id < current.id)
            ):
                winners[key] = policy
        return self.browse([policy.id for policy in winners.values()])
