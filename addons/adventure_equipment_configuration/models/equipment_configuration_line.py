# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Lifecycle states that make a linked asset unsuitable for packing/configuration use.
_UNAVAILABLE_LIFECYCLES = frozenset(
    {
        "retired",
        "lost",
        "stolen",
        "disposed",
        "transferred",
        "out_for_service",
    }
)


class AdventureEquipmentConfigurationLine(models.Model):
    _name = "adventure.equipment.configuration.line"
    _description = "Equipment List Line"
    _order = "sequence, id"

    configuration_id = fields.Many2one(
        "adventure.equipment.configuration",
        string="List",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        related="configuration_id.partner_id",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="configuration_id.company_id",
        store=True,
        index=True,
    )
    sequence = fields.Integer(default=10)
    line_type = fields.Selection(
        selection=[
            ("asset", "Equipment"),
            ("text", "Custom item"),
            ("quantity", "Quantity"),
        ],
        string="Line type",
        required=True,
        default="asset",
    )
    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        string="Equipment",
        ondelete="set null",
        index=True,
    )
    asset_snapshot_name = fields.Char(
        string="Equipment snapshot",
        help="Denormalized equipment label captured when linking; survives hard delete.",
    )
    name = fields.Char(
        string="Label",
        help="Display label. Required for custom/quantity lines; optional override for assets.",
    )
    category_id = fields.Many2one(
        "adventure.equipment.category",
        string="Category hint",
        ondelete="set null",
    )
    role_code = fields.Char(
        string="Role",
        help="Sport-agnostic role code, e.g. primary_reg, backup_light.",
    )
    quantity = fields.Float(string="Quantity")
    quantity_uom_label = fields.Char(
        string="Unit",
        help="Free-text unit label such as lb, kg, or cu ft.",
    )
    notes = fields.Text()
    is_checked = fields.Boolean(string="Checked", default=False)
    reference_state = fields.Selection(
        selection=[
            ("ok", "OK"),
            ("archived", "Archived"),
            ("unavailable", "Unavailable"),
            ("missing", "Missing"),
        ],
        compute="_compute_reference_state",
        store=True,
        index=True,
    )
    display_label = fields.Char(compute="_compute_display_label")

    @api.depends(
        "asset_id",
        "asset_id.active",
        "asset_id.lifecycle_state",
        "line_type",
        "asset_snapshot_name",
        "name",
    )
    def _compute_reference_state(self):
        Asset = self.env["adventure.equipment.asset"].with_context(active_test=False)
        for line in self:
            if line.line_type in ("text", "quantity") and not line.asset_id:
                line.reference_state = "ok"
                continue
            if not line.asset_id:
                # Asset-linked row whose equipment was hard-deleted, or incomplete asset line.
                if line.asset_snapshot_name or line.line_type == "asset":
                    line.reference_state = "missing"
                else:
                    line.reference_state = "ok"
                continue
            asset = Asset.browse(line.asset_id.id)
            if not asset.exists():
                line.reference_state = "missing"
            elif not asset.active:
                line.reference_state = "archived"
            elif asset.lifecycle_state in _UNAVAILABLE_LIFECYCLES:
                line.reference_state = "unavailable"
            else:
                line.reference_state = "ok"

    @api.depends("name", "asset_id", "asset_id.display_name", "asset_snapshot_name", "quantity", "quantity_uom_label")
    def _compute_display_label(self):
        for line in self:
            if line.name:
                line.display_label = line.name
            elif line.asset_id:
                line.display_label = line.asset_id.display_name
            elif line.asset_snapshot_name:
                line.display_label = line.asset_snapshot_name
            elif line.line_type == "quantity" and (line.quantity or line.quantity_uom_label):
                qty = line.quantity if line.quantity else ""
                uom = line.quantity_uom_label or ""
                line.display_label = ("%s %s" % (qty, uom)).strip() or _("Quantity item")
            else:
                line.display_label = _("Untitled item")

    @api.onchange("asset_id")
    def _onchange_asset_id(self):
        if self.asset_id:
            self.asset_snapshot_name = self.asset_id.display_name
            if not self.name:
                self.name = self.asset_id.display_name
            if self.line_type != "asset":
                self.line_type = "asset"

    @api.constrains("asset_id", "configuration_id", "partner_id")
    def _check_asset_owner(self):
        for line in self:
            if not line.asset_id:
                continue
            if line.asset_id.partner_id != line.configuration_id.partner_id:
                raise ValidationError(
                    _(
                        "Equipment on a list must belong to the same customer as the list."
                    )
                )

    @api.constrains("line_type", "asset_id", "name", "quantity", "quantity_uom_label")
    def _check_line_content(self):
        for line in self:
            if line.line_type == "text" and not (line.name or "").strip():
                raise ValidationError(_("Custom items need a label."))
            if line.line_type == "quantity" and not (
                line.name or line.quantity or line.quantity_uom_label
            ):
                raise ValidationError(
                    _("Quantity lines need a label, quantity, or unit.")
                )
            if line.line_type == "asset" and not line.asset_id and not line.asset_snapshot_name:
                raise ValidationError(
                    _("Equipment lines need a linked equipment item.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        Asset = self.env["adventure.equipment.asset"].sudo()
        Config = self.env["adventure.equipment.configuration"].sudo()
        # Track next sequence per configuration within this batch so tied
        # defaults (all sequence=10) do not leave portal adds unordered.
        next_seq_by_config = {}
        for vals in vals_list:
            asset_id = vals.get("asset_id")
            if asset_id:
                asset = Asset.browse(asset_id)
                config = Config.browse(vals.get("configuration_id"))
                if config and asset.partner_id != config.partner_id:
                    raise ValidationError(
                        _(
                            "Equipment on a list must belong to the same customer as the list."
                        )
                    )
                if not vals.get("asset_snapshot_name"):
                    vals["asset_snapshot_name"] = asset.display_name
                if not vals.get("name"):
                    vals["name"] = asset.display_name
                if asset_id and vals.get("line_type") not in ("asset", "text", "quantity"):
                    vals["line_type"] = "asset"
                elif not vals.get("line_type"):
                    vals["line_type"] = "asset"
            config_id = vals.get("configuration_id")
            if config_id and "sequence" not in vals:
                if config_id not in next_seq_by_config:
                    last = self.search(
                        [("configuration_id", "=", config_id)],
                        order="sequence desc, id desc",
                        limit=1,
                    )
                    next_seq_by_config[config_id] = (last.sequence if last else 0) + 10
                vals["sequence"] = next_seq_by_config[config_id]
                next_seq_by_config[config_id] += 10
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("asset_id"):
            asset = self.env["adventure.equipment.asset"].sudo().browse(vals["asset_id"])
            for line in self:
                if asset.partner_id != line.configuration_id.partner_id:
                    raise ValidationError(
                        _(
                            "Equipment on a list must belong to the same customer as the list."
                        )
                    )
            if "asset_snapshot_name" not in vals:
                vals = dict(vals, asset_snapshot_name=asset.display_name)
        return super().write(vals)

    def _ordered_sibling_lines(self):
        self.ensure_one()
        return self.search(
            [("configuration_id", "=", self.configuration_id.id)],
            order="sequence asc, id asc",
        )

    def _resequence_lines(self, lines):
        """Assign unique ascending sequences so display order matches list order."""
        for index, line in enumerate(lines):
            new_seq = (index + 1) * 10
            if line.sequence != new_seq:
                line.sequence = new_seq

    def action_move_up(self):
        """Move this line one position earlier in display order."""
        self.ensure_one()
        lines = list(self._ordered_sibling_lines())
        idx = next((i for i, line in enumerate(lines) if line.id == self.id), None)
        if idx is None or idx == 0:
            return True
        lines[idx - 1], lines[idx] = lines[idx], lines[idx - 1]
        self._resequence_lines(lines)
        return True

    def action_move_down(self):
        """Move this line one position later in display order."""
        self.ensure_one()
        lines = list(self._ordered_sibling_lines())
        idx = next((i for i, line in enumerate(lines) if line.id == self.id), None)
        if idx is None or idx >= len(lines) - 1:
            return True
        lines[idx + 1], lines[idx] = lines[idx], lines[idx + 1]
        self._resequence_lines(lines)
        return True

    def action_toggle_checked(self):
        for line in self:
            line.is_checked = not line.is_checked
        return True