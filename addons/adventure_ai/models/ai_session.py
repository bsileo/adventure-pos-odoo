# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AdventureAiSession(models.Model):
    _name = "adventure.ai.session"
    _description = "Adventure AI Session"
    _order = "write_date desc, id desc"

    name = fields.Char(required=True, default="AI Session")
    user_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        index=True,
    )
    profile = fields.Char(
        required=True,
        default="default",
        help="Capability pack / agent profile, e.g. pos_retail.",
    )
    channel = fields.Selection(
        [
            ("pos", "POS"),
            ("backend", "Backend"),
            ("portal", "Portal"),
            ("system", "System"),
        ],
        required=True,
        default="backend",
        index=True,
    )
    state = fields.Selection(
        [
            ("open", "Open"),
            ("closed", "Closed"),
        ],
        required=True,
        default="open",
        index=True,
    )
    turn_ids = fields.One2many("adventure.ai.turn", "session_id", string="Turns")
    usage_ids = fields.One2many("adventure.ai.usage", "session_id", string="Usage")
    turn_count = fields.Integer(compute="_compute_turn_count")
    last_error = fields.Text(copy=False)

    @api.depends("turn_ids")
    def _compute_turn_count(self):
        for session in self:
            session.turn_count = len(session.turn_ids)

    def action_close(self):
        self.write({"state": "closed"})


class AdventureAiTurn(models.Model):
    _name = "adventure.ai.turn"
    _description = "Adventure AI Turn"
    _order = "id asc"

    session_id = fields.Many2one(
        "adventure.ai.session",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    role = fields.Selection(
        [
            ("user", "User"),
            ("assistant", "Assistant"),
            ("tool", "Tool"),
            ("system", "System"),
        ],
        required=True,
    )
    content = fields.Text()
    tool_name = fields.Char()
    tool_call_id = fields.Char()
    payload_json = fields.Json(string="Payload")
