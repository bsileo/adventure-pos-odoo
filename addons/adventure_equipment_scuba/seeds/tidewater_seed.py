# -*- coding: utf-8 -*-
"""Tidewater Dive Shop contributor for customer-owned scuba equipment.

Owned by adventure_equipment_scuba. Links to dive_shop_pos_seed customer XML ids.
Skip-safe when partners or the scuba module models are unavailable.
"""

from datetime import timedelta

from odoo import fields


SEED_MODULE = "adventure_equipment_scuba_seed"
CUSTOMER_MODULE = "dive_shop_pos_seed"


class TidewaterEquipmentScubaSeed:
    """Seed customer equipment assets for Tidewater story customers."""

    def __init__(self, env, reset=False):
        self.env = env
        self.reset_requested = reset
        self.imd = env["ir.model.data"].sudo()
        self.created = []
        self.updated = []
        self.stats = {"skipped": False}

    def run(self):
        if "adventure.equipment.asset" not in self.env:
            self.stats["skipped"] = True
            self.stats["reason"] = "adventure_equipment not loaded"
            return self.stats

        module = (
            self.env["ir.module.module"]
            .sudo()
            .search(
                [("name", "=", "adventure_equipment_scuba"), ("state", "=", "installed")],
                limit=1,
            )
        )
        if not module:
            self.stats["skipped"] = True
            self.stats["reason"] = "adventure_equipment_scuba not installed"
            return self.stats

        partners = self._load_partners()
        if not partners:
            self.stats["skipped"] = True
            self.stats["reason"] = "Tidewater customers not seeded yet"
            return self.stats

        if self.reset_requested:
            self.stats["deleted"] = self._reset()

        assets = self._seed_assets(partners)
        self._sync_requirements(assets)
        self._seed_service_history()
        self._sync_requirements(assets)
        if hasattr(assets, "action_sync_scuba_service_dates_from_history"):
            assets.action_sync_scuba_service_dates_from_history()

        self.stats.update(
            {
                "created": len(self.created),
                "updated": len(self.updated),
                "equipment_assets": len(assets),
            }
        )
        return self.stats

    def _load_partners(self):
        keys = (
            "customer_certified_current",
            "customer_certified_expired_waiver",
            "customer_uncertified",
            "customer_nitrox",
            "customer_group",
        )
        partners = {}
        for key in keys:
            partner = self.env.ref("%s.%s" % (CUSTOMER_MODULE, key), raise_if_not_found=False)
            if partner:
                partners[key] = partner.sudo()
        return partners

    def _ref(self, xml_name):
        return self.env.ref("%s.%s" % (SEED_MODULE, xml_name), raise_if_not_found=False)

    def _upsert(self, model_name, xml_name, values):
        model = self.env[model_name].sudo()
        values = {key: value for key, value in values.items() if key in model._fields}
        record = self._ref(xml_name)
        if record and record.exists():
            # Service records that are already completed should not be rewritten into draft.
            if model_name == "adventure.equipment.service.record" and record.state in (
                "completed",
                "verified",
                "voided",
            ):
                self.updated.append((model_name, xml_name))
                return record
            record.write(values)
            self.updated.append((model_name, xml_name))
            return record

        record = model.create(values)
        self.imd.create(
            {
                "module": SEED_MODULE,
                "name": xml_name,
                "model": model_name,
                "res_id": record.id,
                "noupdate": True,
            }
        )
        self.created.append((model_name, xml_name))
        return record

    def _reset(self):
        deleted = 0
        # Completed service records refuse unlink; force draft then delete.
        record_xmls = self.imd.search(
            [
                ("module", "=", SEED_MODULE),
                ("model", "=", "adventure.equipment.service.record"),
            ]
        )
        for xml_record in record_xmls:
            record = (
                self.env["adventure.equipment.service.record"]
                .sudo()
                .browse(xml_record.res_id)
            )
            if record.exists():
                if record.state != "draft":
                    record.with_context(equipment_service_force_write=True).write(
                        {"state": "draft"}
                    )
                record.unlink()
                deleted += 1
            if xml_record.exists():
                xml_record.unlink()

        asset_xmls = self.imd.search(
            [("module", "=", SEED_MODULE), ("model", "=", "adventure.equipment.asset")]
        )
        for xml_record in asset_xmls:
            record = (
                self.env["adventure.equipment.asset"].sudo().browse(xml_record.res_id)
            )
            if record.exists():
                record.unlink()
                deleted += 1
            if xml_record.exists():
                xml_record.unlink()
        return deleted

    def _cat(self, xmlid_suffix):
        return self.env.ref("adventure_equipment.equipment_category_%s" % xmlid_suffix)

    def _seed_assets(self, partners):
        Asset = self.env["adventure.equipment.asset"].sudo()
        company = self.env.ref("base.main_company").sudo()
        specs = self._asset_specs(partners, company)
        assets = Asset.browse()
        for xml_name, values in specs:
            assets |= self._upsert("adventure.equipment.asset", xml_name, values)
        return assets

    def _asset_specs(self, partners, company):
        maya = partners.get("customer_certified_current")
        jon = partners.get("customer_certified_expired_waiver")
        nora = partners.get("customer_uncertified")
        luis = partners.get("customer_nitrox")
        family = partners.get("customer_group")
        specs = []

        if maya:
            specs.extend(
                [
                    (
                        "eq_maya_al80",
                        {
                            "partner_id": maya.id,
                            "company_id": company.id,
                            "category_id": self._cat("cylinder").id,
                            "nickname": "Maya AL80",
                            "brand_name": "Luxfer",
                            "model_name": "S80",
                            "serial_number": "TW-CYL-MAYA-AL80",
                            "acquisition_source": "shop_sale",
                            "origin_sale_ref": "POS/2024/118",
                            "lifecycle_state": "active",
                            "in_service_date": "2024-05-12",
                            "purchase_date": "2024-05-12",
                            "condition_state": "excellent",
                            "scuba_cylinder_material": "aluminum",
                            "scuba_water_capacity_l": 11.1,
                            "scuba_working_pressure_bar": 207.0,
                            "scuba_working_pressure_psi": 3000.0,
                            "scuba_gas_compatibility": "air",
                            "scuba_valve_type": "DIN/Yoke",
                            "customer_note": "Primary travel cylinder; kept at Tidewater for fills.",
                        },
                    ),
                    (
                        "eq_maya_regulator",
                        {
                            "partner_id": maya.id,
                            "company_id": company.id,
                            "category_id": self._cat("regulator").id,
                            "nickname": "Maya Primary Reg",
                            "brand_name": "Scubapro",
                            "model_name": "MK25 EVO / S620 Ti",
                            "serial_number": "TW-REG-MAYA-001",
                            "acquisition_source": "shop_sale",
                            "origin_sale_ref": "POS/2024/118",
                            "lifecycle_state": "active",
                            "in_service_date": "2024-05-12",
                            "purchase_date": "2024-05-12",
                            "condition_state": "excellent",
                            "warranty_registered": True,
                            "warranty_start_date": "2024-05-12",
                            "warranty_end_date": "2026-05-12",
                            "scuba_regulator_configuration": "complete_set",
                        },
                    ),
                    (
                        "eq_maya_bcd",
                        {
                            "partner_id": maya.id,
                            "company_id": company.id,
                            "category_id": self._cat("bcd").id,
                            "nickname": "Maya Travel BCD",
                            "brand_name": "Apeks",
                            "model_name": "WTXcx",
                            "serial_number": "TW-BCD-MAYA-001",
                            "acquisition_source": "shop_sale",
                            "lifecycle_state": "active",
                            "in_service_date": "2024-05-12",
                            "purchase_date": "2024-05-12",
                            "condition_state": "good",
                            "scuba_bcd_type": "wing",
                        },
                    ),
                    (
                        "eq_maya_computer",
                        {
                            "partner_id": maya.id,
                            "company_id": company.id,
                            "category_id": self._cat("dive_computer").id,
                            "nickname": "Maya Perdix",
                            "brand_name": "Shearwater",
                            "model_name": "Perdix 2",
                            "serial_number": "TW-DC-MAYA-001",
                            "acquisition_source": "shop_sale",
                            "lifecycle_state": "active",
                            "in_service_date": "2025-01-18",
                            "purchase_date": "2025-01-18",
                            "condition_state": "excellent",
                            "scuba_computer_battery_type": "SAFT LS14500",
                        },
                    ),
                ]
            )

        if jon:
            specs.extend(
                [
                    (
                        "eq_jon_steel72",
                        {
                            "partner_id": jon.id,
                            "company_id": company.id,
                            "category_id": self._cat("cylinder").id,
                            "nickname": "Jon Steel 72",
                            "brand_name": "Faber",
                            "model_name": "LP72",
                            "serial_number": "TW-CYL-JON-LP72",
                            "acquisition_source": "other_shop",
                            "original_seller": "Erie Scuba Outlet",
                            "lifecycle_state": "active",
                            "in_service_date": "2019-03-01",
                            "purchase_date": "2019-03-01",
                            "condition_state": "fair",
                            "scuba_cylinder_material": "steel",
                            "scuba_water_capacity_l": 10.0,
                            "scuba_working_pressure_bar": 179.0,
                            "scuba_working_pressure_psi": 2640.0,
                            "scuba_gas_compatibility": "air",
                            "scuba_valve_type": "Yoke",
                            "customer_note": "VIP overdue — good demo for service desk conversation.",
                        },
                    ),
                    (
                        "eq_jon_regulator",
                        {
                            "partner_id": jon.id,
                            "company_id": company.id,
                            "category_id": self._cat("regulator").id,
                            "nickname": "Jon Backup Reg",
                            "brand_name": "Aqualung",
                            "model_name": "Legend LX",
                            "serial_number": "TW-REG-JON-001",
                            "acquisition_source": "other_shop",
                            "lifecycle_state": "active",
                            "in_service_date": "2022-06-15",
                            "purchase_date": "2022-06-15",
                            "condition_state": "fair",
                            "scuba_regulator_configuration": "complete_set",
                        },
                    ),
                ]
            )

        if luis:
            specs.extend(
                [
                    (
                        "eq_luis_nitrox80",
                        {
                            "partner_id": luis.id,
                            "company_id": company.id,
                            "category_id": self._cat("cylinder").id,
                            "nickname": "Luis Nitrox 80",
                            "brand_name": "Catalina",
                            "model_name": "AL80",
                            "serial_number": "TW-CYL-LUIS-EAN",
                            "acquisition_source": "shop_sale",
                            "origin_sale_ref": "POS/2025/044",
                            "lifecycle_state": "active",
                            "in_service_date": "2025-04-02",
                            "purchase_date": "2025-04-02",
                            "condition_state": "excellent",
                            "scuba_cylinder_material": "aluminum",
                            "scuba_water_capacity_l": 11.1,
                            "scuba_working_pressure_bar": 207.0,
                            "scuba_working_pressure_psi": 3000.0,
                            "scuba_gas_compatibility": "nitrox",
                            "scuba_oxygen_clean": True,
                            "scuba_oxygen_clean_date": "2026-03-10",
                            "scuba_valve_type": "DIN",
                        },
                    ),
                    (
                        "eq_luis_regulator",
                        {
                            "partner_id": luis.id,
                            "company_id": company.id,
                            "category_id": self._cat("regulator").id,
                            "nickname": "Luis O2 Reg",
                            "brand_name": "Hollis",
                            "model_name": "200LX / 150LX",
                            "serial_number": "TW-REG-LUIS-001",
                            "acquisition_source": "shop_sale",
                            "lifecycle_state": "active",
                            "in_service_date": "2025-04-02",
                            "purchase_date": "2025-04-02",
                            "condition_state": "excellent",
                            "scuba_regulator_configuration": "complete_set",
                            "scuba_oxygen_clean": True,
                            "scuba_oxygen_clean_date": "2026-03-10",
                        },
                    ),
                ]
            )

        if nora:
            specs.append(
                (
                    "eq_nora_mfs",
                    {
                        "partner_id": nora.id,
                        "company_id": company.id,
                        "category_id": self._cat("mask_fins_snorkel").id,
                        "nickname": "Nora Snorkel Set",
                        "brand_name": "Cressi",
                        "model_name": "Palau SAF",
                        "acquisition_source": "shop_sale",
                        "origin_sale_ref": "POS/2026/009",
                        "lifecycle_state": "active",
                        "in_service_date": "2026-04-20",
                        "purchase_date": "2026-04-20",
                        "condition_state": "excellent",
                        "warranty_not_applicable": True,
                        "customer_note": "Discover Scuba / snorkel kit — no cylinder yet.",
                    },
                )
            )

        if family:
            specs.append(
                (
                    "eq_family_al80",
                    {
                        "partner_id": family.id,
                        "company_id": company.id,
                        "category_id": self._cat("cylinder").id,
                        "nickname": "Carter Family AL80",
                        "brand_name": "Luxfer",
                        "model_name": "S80",
                        "serial_number": "TW-CYL-FAMILY-AL80",
                        "acquisition_source": "shop_sale",
                        "lifecycle_state": "active",
                        "in_service_date": "2023-08-01",
                        "purchase_date": "2023-08-01",
                        "condition_state": "good",
                        "scuba_cylinder_material": "aluminum",
                        "scuba_water_capacity_l": 11.1,
                        "scuba_working_pressure_bar": 207.0,
                        "scuba_working_pressure_psi": 3000.0,
                        "scuba_gas_compatibility": "air",
                        "scuba_valve_type": "Yoke",
                        "customer_note": "Shared family cylinder for quarry weekends.",
                    },
                )
            )

        return specs

    def _seed_service_history(self):
        """Create completed service history so current customers look current."""
        if "adventure.equipment.service.record" not in self.env:
            return

        today = fields.Date.context_today(self.env.user)
        by_xml = {
            xml_name: self._ref(xml_name)
            for xml_name in (
                "eq_maya_al80",
                "eq_maya_regulator",
                "eq_maya_bcd",
                "eq_luis_nitrox80",
                "eq_luis_regulator",
                "eq_family_al80",
                "eq_jon_steel72",
            )
        }

        vip = self.env.ref(
            "adventure_equipment_scuba.service_type_cylinder_vip",
            raise_if_not_found=False,
        )
        hydro = self.env.ref(
            "adventure_equipment_scuba.service_type_hydrostatic_test",
            raise_if_not_found=False,
        )
        reg_svc = self.env.ref(
            "adventure_equipment_scuba.service_type_regulator_service",
            raise_if_not_found=False,
        )
        bcd_svc = self.env.ref(
            "adventure_equipment_scuba.service_type_bcd_service",
            raise_if_not_found=False,
        )
        o2 = self.env.ref(
            "adventure_equipment_scuba.service_type_oxygen_clean",
            raise_if_not_found=False,
        )

        history = []
        maya_cyl = by_xml.get("eq_maya_al80")
        if maya_cyl and vip:
            history.append(
                (
                    "svc_maya_vip_2026",
                    maya_cyl,
                    vip,
                    today - timedelta(days=90),
                    {
                        "result": "passed",
                        "summary": "Annual VIP at Tidewater fill station.",
                        "scuba_vip_sticker_number": "VIP-TW-2605",
                    },
                )
            )
        if maya_cyl and hydro:
            history.append(
                (
                    "svc_maya_hydro_2023",
                    maya_cyl,
                    hydro,
                    today - timedelta(days=900),
                    {
                        "result": "passed",
                        "summary": "Hydro stamped; due again in five years.",
                        "scuba_hydro_stamp": "A23",
                        "certificate_number": "HYDRO-TW-2023-441",
                    },
                )
            )
        maya_reg = by_xml.get("eq_maya_regulator")
        if maya_reg and reg_svc:
            history.append(
                (
                    "svc_maya_reg_2026",
                    maya_reg,
                    reg_svc,
                    today - timedelta(days=120),
                    {
                        "result": "passed",
                        "summary": "Annual regulator service — IP and cracking pressure OK.",
                    },
                )
            )
        maya_bcd = by_xml.get("eq_maya_bcd")
        if maya_bcd and bcd_svc:
            history.append(
                (
                    "svc_maya_bcd_2026",
                    maya_bcd,
                    bcd_svc,
                    today - timedelta(days=100),
                    {
                        "result": "passed",
                        "summary": "BCD bladder and inflator service.",
                    },
                )
            )

        luis_cyl = by_xml.get("eq_luis_nitrox80")
        if luis_cyl and vip:
            history.append(
                (
                    "svc_luis_vip_2026",
                    luis_cyl,
                    vip,
                    today - timedelta(days=60),
                    {
                        "result": "passed",
                        "summary": "VIP prior to nitrox fill season.",
                        "scuba_vip_sticker_number": "VIP-TW-2603",
                    },
                )
            )
        if luis_cyl and o2:
            history.append(
                (
                    "svc_luis_o2_2026",
                    luis_cyl,
                    o2,
                    today - timedelta(days=150),
                    {
                        "result": "passed",
                        "summary": "Oxygen clean for EAN32 service.",
                        "scuba_oxygen_clean_performed": True,
                    },
                )
            )
        luis_reg = by_xml.get("eq_luis_regulator")
        if luis_reg and reg_svc:
            history.append(
                (
                    "svc_luis_reg_2026",
                    luis_reg,
                    reg_svc,
                    today - timedelta(days=150),
                    {
                        "result": "passed",
                        "summary": "O2-compatible regulator service.",
                        "scuba_oxygen_clean_performed": True,
                    },
                )
            )

        family_cyl = by_xml.get("eq_family_al80")
        if family_cyl and vip:
            history.append(
                (
                    "svc_family_vip_2026",
                    family_cyl,
                    vip,
                    today - timedelta(days=45),
                    {
                        "result": "passed",
                        "summary": "Family cylinder VIP before quarry season.",
                        "scuba_vip_sticker_number": "VIP-TW-2606",
                    },
                )
            )

        # Jon: old VIP so requirements stay overdue after sync (no recent completion).
        jon_cyl = by_xml.get("eq_jon_steel72")
        if jon_cyl and vip:
            history.append(
                (
                    "svc_jon_vip_2023",
                    jon_cyl,
                    vip,
                    today - timedelta(days=700),
                    {
                        "result": "passed",
                        "summary": "Last VIP before Jon stopped bringing the tank in.",
                        "scuba_vip_sticker_number": "VIP-TW-2310",
                    },
                )
            )

        Record = self.env["adventure.equipment.service.record"].sudo()
        for xml_name, asset, service_type, service_date, extra in history:
            if not asset or not asset.exists():
                continue
            values = {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": service_type.id,
                "service_date": service_date,
                "state": "draft",
            }
            values.update(extra)
            values = {k: v for k, v in values.items() if k in Record._fields}
            record = self._upsert("adventure.equipment.service.record", xml_name, values)
            if record.state == "draft":
                record.action_complete()

    def _sync_requirements(self, assets):
        if not assets or "adventure.equipment.service.requirement" not in self.env:
            return
        if hasattr(assets, "action_recalculate_service_requirements"):
            assets.action_recalculate_service_requirements()


def seed_tidewater(env, reset=False):
    return TidewaterEquipmentScubaSeed(env, reset=reset).run()
