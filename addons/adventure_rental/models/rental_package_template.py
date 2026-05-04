# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureRentalPackageTemplate(models.Model):
    _name = "adventure.rental.package.template"
    _description = "Rental Package Template"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one("product.product", string="Package Product")
    component_payload = fields.Json(default=list)
    requirement_payload = fields.Json(default=dict)
