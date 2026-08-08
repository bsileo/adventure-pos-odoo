# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AdventureEquipmentAsset(models.Model):
    _inherit = "adventure.equipment.asset"

    # ------------------------------------------------------------------
    # Scuba classification helpers
    # ------------------------------------------------------------------

    is_scuba_cylinder = fields.Boolean(
        compute="_compute_scuba_category_flags",
        store=True,
    )
    is_scuba_regulator = fields.Boolean(
        compute="_compute_scuba_category_flags",
        store=True,
    )
    is_scuba_bcd = fields.Boolean(
        compute="_compute_scuba_category_flags",
        store=True,
    )
    is_scuba_computer = fields.Boolean(
        compute="_compute_scuba_category_flags",
        store=True,
    )
    is_scuba_exposure_suit = fields.Boolean(
        compute="_compute_scuba_category_flags",
        store=True,
    )
    show_scuba_panel = fields.Boolean(
        compute="_compute_scuba_category_flags",
        store=True,
    )

    # ------------------------------------------------------------------
    # Cylinder / gas metadata
    # ------------------------------------------------------------------

    scuba_cylinder_material = fields.Selection(
        [
            ("aluminum", "Aluminum"),
            ("steel", "Steel"),
            ("carbon_fiber", "Carbon Fiber"),
            ("other", "Other"),
        ],
        string="Cylinder Material",
        tracking=True,
    )
    scuba_working_pressure_bar = fields.Float(
        string="Working Pressure (bar)",
        digits=(16, 1),
        tracking=True,
    )
    scuba_working_pressure_psi = fields.Float(
        string="Working Pressure (psi)",
        digits=(16, 1),
        tracking=True,
    )
    scuba_test_pressure_bar = fields.Float(
        string="Test Pressure (bar)",
        digits=(16, 1),
    )
    scuba_water_capacity_l = fields.Float(
        string="Water Capacity (L)",
        digits=(16, 2),
        help="Internal water capacity in litres (e.g. 11.1 for AL80).",
    )
    scuba_gas_compatibility = fields.Selection(
        [
            ("air", "Air"),
            ("nitrox", "Nitrox (EAN)"),
            ("oxygen", "Oxygen"),
            ("trimix", "Trimix"),
            ("other", "Other"),
        ],
        string="Gas Compatibility",
        default="air",
        tracking=True,
    )
    scuba_oxygen_clean = fields.Boolean(
        string="Oxygen Clean",
        tracking=True,
        help="Cylinder / regulator cleaned and suitable for elevated oxygen service.",
    )
    scuba_oxygen_clean_date = fields.Date(string="Oxygen Clean Date")
    scuba_valve_type = fields.Char(
        string="Valve Type",
        help="e.g. K-valve, DIN, yoke converter.",
    )
    scuba_hydro_stamp = fields.Char(
        string="Hydro Stamp / Mark",
        tracking=True,
    )
    scuba_last_vip_date = fields.Date(
        string="Last VIP Date",
        tracking=True,
        help="Denormalized from the latest completed VIP service record when available.",
    )
    scuba_last_hydro_date = fields.Date(
        string="Last Hydro Date",
        tracking=True,
        help="Denormalized from the latest completed hydrostatic service record when available.",
    )

    # ------------------------------------------------------------------
    # Regulator / BCD / computer / suit
    # ------------------------------------------------------------------

    scuba_regulator_configuration = fields.Selection(
        [
            ("primary", "Primary"),
            ("octopus", "Octopus / Alternate"),
            ("complete_set", "Complete Set"),
            ("first_stage_only", "First Stage Only"),
            ("second_stage_only", "Second Stage Only"),
            ("other", "Other"),
        ],
        string="Regulator Configuration",
    )
    scuba_bcd_type = fields.Selection(
        [
            ("jacket", "Jacket"),
            ("wing", "Wing / Backplate"),
            ("hybrid", "Hybrid"),
            ("other", "Other"),
        ],
        string="BCD Type",
    )
    scuba_suit_type = fields.Selection(
        [
            ("wetsuit", "Wetsuit"),
            ("drysuit", "Drysuit"),
            ("semidry", "Semi-Dry"),
            ("skins", "Skins"),
            ("other", "Other"),
        ],
        string="Exposure Suit Type",
    )
    scuba_computer_battery_type = fields.Char(string="Computer Battery Type")
    scuba_notes = fields.Text(
        string="Scuba Notes",
        groups="adventure_equipment.group_equipment_user",
    )

    @api.depends("category_id", "category_id.code")
    def _compute_scuba_category_flags(self):
        for asset in self:
            code = (asset.category_id.code or "").upper()
            asset.is_scuba_cylinder = code == "CYL"
            asset.is_scuba_regulator = code == "REG"
            asset.is_scuba_bcd = code == "BCD"
            asset.is_scuba_computer = code == "DC"
            asset.is_scuba_exposure_suit = code == "SUIT"
            asset.show_scuba_panel = code in {
                "CYL",
                "REG",
                "BCD",
                "DC",
                "SUIT",
                "LIGHT",
            }

    def action_sync_scuba_service_dates_from_history(self):
        """Refresh denormalized VIP/hydro dates from completed service records."""
        vip = self.env.ref(
            "adventure_equipment_scuba.service_type_cylinder_vip",
            raise_if_not_found=False,
        )
        hydro = self.env.ref(
            "adventure_equipment_scuba.service_type_hydrostatic_test",
            raise_if_not_found=False,
        )
        Record = self.env["adventure.equipment.service.record"]
        for asset in self:
            vals = {}
            if vip:
                last_vip = Record.search(
                    [
                        ("asset_id", "=", asset.id),
                        ("service_type_id", "=", vip.id),
                        ("state", "in", ("completed", "verified")),
                    ],
                    order="service_date desc, id desc",
                    limit=1,
                )
                vals["scuba_last_vip_date"] = last_vip.service_date if last_vip else False
            if hydro:
                last_hydro = Record.search(
                    [
                        ("asset_id", "=", asset.id),
                        ("service_type_id", "=", hydro.id),
                        ("state", "in", ("completed", "verified")),
                    ],
                    order="service_date desc, id desc",
                    limit=1,
                )
                vals["scuba_last_hydro_date"] = (
                    last_hydro.service_date if last_hydro else False
                )
                if last_hydro and last_hydro.scuba_hydro_stamp:
                    vals["scuba_hydro_stamp"] = last_hydro.scuba_hydro_stamp
            if vals:
                asset.write(vals)
        return True
