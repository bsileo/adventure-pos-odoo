# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AdventureEquipmentServiceType(models.Model):
    _name = "adventure.equipment.service.type"
    _description = "Equipment Service Type"
    _order = "sequence, name, id"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, tracking=True, translate=True)
    code = fields.Char(tracking=True, index=True)
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10)
    description = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        help="Leave empty for a shared type available to all companies.",
    )
    classification = fields.Selection(
        [
            ("service", "Service"),
            ("inspection", "Inspection"),
            ("certification", "Certification"),
            ("test", "Test"),
            ("preventive", "Preventive Maintenance"),
            ("other", "Other"),
        ],
        default="inspection",
        required=True,
        tracking=True,
    )
    customer_name = fields.Char(
        string="Customer-Facing Name",
        translate=True,
        help="Optional label shown to customers when portal is enabled.",
    )
    customer_description = fields.Text(translate=True)
    internal_instructions = fields.Html(
        groups="adventure_equipment.group_equipment_user",
    )
    requires_result = fields.Boolean(
        string="Requires Pass/Fail Result",
        default=True,
    )
    requires_certificate = fields.Boolean(
        string="Requires Certificate/Reference",
    )
    supports_expiration = fields.Boolean(default=True)
    supports_recurring = fields.Boolean(
        string="Supports Recurring Scheduling",
        default=True,
    )
    default_warning_lead_days = fields.Integer(
        string="Default Warning Lead Days",
        default=30,
    )
    default_grace_days = fields.Integer(
        string="Default Grace Days",
        default=0,
    )
    tag_ids = fields.Many2many(
        "adventure.equipment.tag",
        "adventure_equipment_service_type_tag_rel",
        "type_id",
        "tag_id",
        string="Tags",
    )
    notes = fields.Text()
    policy_ids = fields.One2many(
        "adventure.equipment.service.policy",
        "service_type_id",
        string="Policies",
    )
    policy_count = fields.Integer(compute="_compute_policy_count")

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "Service type code must be unique per company.",
    )

    @api.depends("policy_ids")
    def _compute_policy_count(self):
        for row in self:
            row.policy_count = len(row.policy_ids)
