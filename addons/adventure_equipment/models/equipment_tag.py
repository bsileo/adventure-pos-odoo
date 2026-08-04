# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureEquipmentTag(models.Model):
    _name = "adventure.equipment.tag"
    _description = "Equipment Tag"
    _order = "name, id"

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(string="Color Index", default=0)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        help="Leave empty for tags shared across companies in this database.",
    )
    active = fields.Boolean(default=True)
