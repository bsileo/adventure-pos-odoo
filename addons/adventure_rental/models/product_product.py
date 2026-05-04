# -*- coding: utf-8 -*-

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        for field_name in ("is_rental", "tracking"):
            if field_name not in fields:
                fields.append(field_name)
        return fields
