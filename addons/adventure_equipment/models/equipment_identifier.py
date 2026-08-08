# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AdventureEquipmentIdentifier(models.Model):
    _name = "adventure.equipment.identifier"
    _description = "Equipment Identifier"
    _order = "primary desc, id_type, name, id"

    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        string="Equipment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    id_type = fields.Selection(
        [
            ("serial", "Serial Number"),
            ("manufacturer_serial", "Manufacturer Serial"),
            ("shop_tag", "Shop Tag"),
            ("barcode", "Barcode"),
            ("rfid", "RFID"),
            ("manufacturer_registration", "Manufacturer Registration"),
            ("other", "Other"),
        ],
        string="Identifier Type",
        required=True,
        default="serial",
        index=True,
    )
    name = fields.Char(
        string="Value",
        required=True,
        index=True,
    )
    issuer = fields.Char(
        help="Organization or system that issued this identifier.",
    )
    primary = fields.Boolean(
        string="Primary",
        default=False,
        help="Primary identifier of this type for the equipment record.",
    )
    notes = fields.Text()
    date_recorded = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="asset_id.company_id",
        store=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name"):
                vals["name"] = vals["name"].strip()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("name"):
            vals["name"] = vals["name"].strip()
        return super().write(vals)

    @api.constrains("asset_id", "id_type", "primary")
    def _check_single_primary_per_type(self):
        for identifier in self:
            if not identifier.primary:
                continue
            duplicate_count = self.search_count(
                [
                    ("id", "!=", identifier.id),
                    ("asset_id", "=", identifier.asset_id.id),
                    ("id_type", "=", identifier.id_type),
                    ("primary", "=", True),
                ]
            )
            if duplicate_count:
                raise ValidationError(
                    _(
                        "Only one primary %(id_type)s identifier is allowed per equipment record.",
                        id_type=dict(
                            self._fields["id_type"].selection
                        ).get(identifier.id_type),
                    )
                )
