# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    adventure_pos_dev_note = fields.Char(
        string="POS dev note",
        help="Optional label for local dev / smoke tests (Adventure POS).",
    )
