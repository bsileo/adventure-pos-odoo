# -*- coding: utf-8 -*-

from odoo import fields, models

from .adventure_waiver import (
    PARAM_API_KEY,
    PARAM_BASE_URL,
    PARAM_ENABLED,
    PARAM_FETCH_PDF_DEFAULT,
    PARAM_TEMPLATE_IDS,
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    smartwaiver_api_key = fields.Char(
        string="Smartwaiver API key",
        config_parameter=PARAM_API_KEY,
        help="Stored in system parameters. Prefer SMARTWAIVER_API_KEY env var in "
        "shared environments. Never commit secrets.",
    )
    smartwaiver_sync_enabled = fields.Boolean(
        string="Enable Smartwaiver sync",
        config_parameter=PARAM_ENABLED,
    )
    smartwaiver_base_url = fields.Char(
        string="Smartwaiver API base URL",
        config_parameter=PARAM_BASE_URL,
        default="https://api.smartwaiver.com",
    )
    smartwaiver_template_ids = fields.Char(
        string="Template allowlist",
        config_parameter=PARAM_TEMPLATE_IDS,
        help="Comma-separated Smartwaiver template IDs. Empty = all templates.",
    )
    smartwaiver_fetch_pdf_default = fields.Boolean(
        string="Prefer storing PDFs when fetched",
        config_parameter=PARAM_FETCH_PDF_DEFAULT,
        help="Informational for staff; PDFs are still fetched on demand in V1.",
    )

    def action_smartwaiver_sync_now(self):
        self.ensure_one()
        return self.env["adventure.waiver"].action_smartwaiver_sync_now()
