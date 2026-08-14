# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AdventureEquipmentConfiguration(models.Model):
    _name = "adventure.equipment.configuration"
    _description = "Equipment Packing List or Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name, id"

    name = fields.Char(required=True, tracking=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        index=True,
        tracking=True,
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    list_kind = fields.Selection(
        selection=[
            ("packing", "Packing list"),
            ("configuration", "Configuration"),
        ],
        string="Kind",
        required=True,
        default="packing",
        tracking=True,
        index=True,
    )
    active = fields.Boolean(default=True)
    description = fields.Text()
    customer_note = fields.Text(
        string="Notes",
        help="Customer-visible notes about this list or setup over time.",
    )
    sequence = fields.Integer(default=10)
    color = fields.Integer(string="Color Index")
    line_ids = fields.One2many(
        "adventure.equipment.configuration.line",
        "configuration_id",
        string="Lines",
        copy=True,
    )
    line_count = fields.Integer(compute="_compute_line_count")
    has_broken_references = fields.Boolean(
        compute="_compute_has_broken_references",
        store=True,
        index=True,
    )

    @api.depends("line_ids")
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    @api.depends(
        "line_ids.reference_state",
        "line_ids.asset_id",
        "line_ids.asset_id.active",
        "line_ids.asset_id.lifecycle_state",
        "line_ids.line_type",
        "line_ids.asset_snapshot_name",
    )
    def _compute_has_broken_references(self):
        for record in self:
            record.has_broken_references = any(
                line.reference_state != "ok" for line in record.line_ids
            )

    @api.constrains("list_kind")
    def _check_list_kind_immutable_with_lines(self):
        # Constrains alone cannot see old values; enforce in write().
        return

    def write(self, vals):
        if "list_kind" in vals:
            for record in self:
                if record.line_ids and vals["list_kind"] != record.list_kind:
                    raise ValidationError(
                        _(
                            "You cannot change the list kind after lines have been "
                            "added. Create a new packing list or configuration instead."
                        )
                    )
        return super().write(vals)

    def action_reset_checks(self):
        self.ensure_one()
        self.line_ids.write({"is_checked": False})
        return True
