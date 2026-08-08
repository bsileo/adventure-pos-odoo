# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AdventureEquipmentServiceRecord(models.Model):
    _inherit = "adventure.equipment.service.record"

    scuba_vip_sticker_number = fields.Char(string="VIP Sticker Number")
    scuba_hydro_stamp = fields.Char(string="Hydro Stamp / Mark")
    scuba_oxygen_clean_performed = fields.Boolean(string="Oxygen Clean Performed")
    scuba_max_oxygen_percent = fields.Float(
        string="Max O₂ % Certified",
        digits=(16, 1),
        help="Highest oxygen percentage this service certified the equipment for.",
    )
    scuba_visual_findings_code = fields.Selection(
        [
            ("pass", "Pass"),
            ("pass_with_notes", "Pass with Notes"),
            ("fail", "Fail"),
            ("condemn", "Condemn / Remove from Service"),
        ],
        string="VIP / Visual Result Detail",
    )

    def action_complete(self):
        res = super().action_complete()
        self._scuba_update_asset_denorm()
        return res

    def _scuba_update_asset_denorm(self):
        vip = self.env.ref(
            "adventure_equipment_scuba.service_type_cylinder_vip",
            raise_if_not_found=False,
        )
        hydro = self.env.ref(
            "adventure_equipment_scuba.service_type_hydrostatic_test",
            raise_if_not_found=False,
        )
        o2 = self.env.ref(
            "adventure_equipment_scuba.service_type_oxygen_clean",
            raise_if_not_found=False,
        )
        for row in self:
            if row.state not in ("completed", "verified"):
                continue
            vals = {}
            if vip and row.service_type_id == vip:
                vals["scuba_last_vip_date"] = row.service_date
            if hydro and row.service_type_id == hydro:
                vals["scuba_last_hydro_date"] = row.service_date
                if row.scuba_hydro_stamp:
                    vals["scuba_hydro_stamp"] = row.scuba_hydro_stamp
            if o2 and row.service_type_id == o2 and row.scuba_oxygen_clean_performed:
                vals["scuba_oxygen_clean"] = True
                vals["scuba_oxygen_clean_date"] = row.service_date
            elif row.scuba_oxygen_clean_performed:
                vals["scuba_oxygen_clean"] = True
                vals["scuba_oxygen_clean_date"] = row.service_date
            if vals:
                row.asset_id.write(vals)
