# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureEquipmentCategory(models.Model):
    """Sport-agnostic equipment taxonomy (independent of product.category)."""

    _name = "adventure.equipment.category"
    _description = "Equipment Category"
    _order = "sequence, name"
    _parent_store = True

    name = fields.Char(required=True, translate=True)
    code = fields.Char(index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()
    parent_id = fields.Many2one(
        "adventure.equipment.category",
        string="Parent",
        index=True,
        ondelete="restrict",
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        "adventure.equipment.category",
        "parent_id",
        string="Children",
    )
    is_serviceable = fields.Boolean(
        string="Default serviceable",
        default=True,
        help="Hint for later service modules; no policies are enforced in core.",
    )
    is_durable = fields.Boolean(
        string="Durable equipment",
        default=True,
        help="Marks long-lived physical items vs consumables.",
    )
    payload = fields.Json(
        default=dict,
        help="Extension hook for sport-specific attributes until promoted to fields.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        help="Leave empty for shared categories across companies in this database.",
    )
