# -*- coding: utf-8 -*-

from odoo import fields, models


class AdventureAiUsage(models.Model):
    _name = "adventure.ai.usage"
    _description = "Adventure AI Usage"
    _order = "create_date desc, id desc"

    session_id = fields.Many2one(
        "adventure.ai.session",
        ondelete="set null",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        index=True,
    )
    feature = fields.Char(
        required=True,
        default="general",
        index=True,
        help="Commercial / domain feature tag, e.g. pos_retail.",
    )
    capability_name = fields.Char(index=True)
    provider = fields.Char(required=True, default="mock")
    model = fields.Char()
    channel = fields.Char()
    profile = fields.Char()
    input_tokens = fields.Integer(default=0)
    output_tokens = fields.Integer(default=0)
    estimated_cost = fields.Float(digits=(16, 6), default=0.0)
    latency_ms = fields.Integer(default=0)
    success = fields.Boolean(default=True)
    error_message = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
