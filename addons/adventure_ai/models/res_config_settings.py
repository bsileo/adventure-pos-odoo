# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    adventure_ai_provider = fields.Selection(
        [
            ("mock", "Mock (no API key; for tests and demos)"),
            ("openai", "OpenAI"),
        ],
        string="AI Provider",
        config_parameter="adventure_ai.provider",
        default="mock",
    )
    adventure_ai_openai_api_key = fields.Char(
        string="OpenAI API Key",
        config_parameter="adventure_ai.openai_api_key",
    )
    adventure_ai_openai_model = fields.Char(
        string="OpenAI Model",
        config_parameter="adventure_ai.openai_model",
        default="gpt-4o-mini",
    )
    adventure_ai_openai_base_url = fields.Char(
        string="OpenAI Base URL",
        config_parameter="adventure_ai.openai_base_url",
        default="https://api.openai.com/v1",
    )

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("adventure_ai.provider", self.adventure_ai_provider or "mock")
        ICP.set_param(
            "adventure_ai.openai_api_key", self.adventure_ai_openai_api_key or ""
        )
        ICP.set_param(
            "adventure_ai.openai_model", self.adventure_ai_openai_model or "gpt-4o-mini"
        )
        ICP.set_param(
            "adventure_ai.openai_base_url",
            self.adventure_ai_openai_base_url or "https://api.openai.com/v1",
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        res.update(
            adventure_ai_provider=ICP.get_param("adventure_ai.provider") or "mock",
            adventure_ai_openai_api_key=ICP.get_param("adventure_ai.openai_api_key") or "",
            adventure_ai_openai_model=ICP.get_param("adventure_ai.openai_model")
            or "gpt-4o-mini",
            adventure_ai_openai_base_url=ICP.get_param("adventure_ai.openai_base_url")
            or "https://api.openai.com/v1",
        )
        return res
