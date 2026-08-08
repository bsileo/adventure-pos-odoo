# -*- coding: utf-8 -*-

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAdventureEquipmentScubaAssetFields(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Scuba Field Customer"})
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.Record = cls.env["adventure.equipment.service.record"]
        cls.cyl_cat = cls.env.ref("adventure_equipment.equipment_category_cylinder")
        cls.reg_cat = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.vip = cls.env.ref("adventure_equipment_scuba.service_type_cylinder_vip")
        cls.hydro = cls.env.ref("adventure_equipment_scuba.service_type_hydrostatic_test")
        cls.o2 = cls.env.ref("adventure_equipment_scuba.service_type_oxygen_clean")

    def test_category_flags(self):
        cyl = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.cyl_cat.id,
            }
        )
        reg = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.reg_cat.id,
            }
        )
        self.assertTrue(cyl.is_scuba_cylinder)
        self.assertTrue(cyl.show_scuba_panel)
        self.assertTrue(reg.is_scuba_regulator)
        self.assertFalse(reg.is_scuba_cylinder)

    def test_vip_completion_updates_denorm_dates(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.cyl_cat.id,
                "lifecycle_state": "active",
                "in_service_date": "2024-01-01",
                "scuba_gas_compatibility": "air",
            }
        )
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.vip.id,
                "service_date": date(2025, 3, 15),
                "result": "passed",
                "scuba_vip_sticker_number": "VIP-123",
                "scuba_visual_findings_code": "pass",
            }
        )
        record.action_complete()
        self.assertEqual(asset.scuba_last_vip_date, date(2025, 3, 15))

    def test_hydro_and_oxygen_clean_update_asset(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.cyl_cat.id,
                "lifecycle_state": "active",
                "in_service_date": "2020-01-01",
            }
        )
        hydro = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.hydro.id,
                "service_date": date(2025, 1, 10),
                "result": "passed",
                "certificate_number": "HYDRO-999",
                "scuba_hydro_stamp": "1 25 A",
            }
        )
        hydro.action_complete()
        self.assertEqual(asset.scuba_last_hydro_date, date(2025, 1, 10))
        self.assertEqual(asset.scuba_hydro_stamp, "1 25 A")

        o2 = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.o2.id,
                "service_date": date(2025, 2, 1),
                "result": "passed",
                "scuba_oxygen_clean_performed": True,
                "scuba_max_oxygen_percent": 40.0,
            }
        )
        o2.action_complete()
        self.assertTrue(asset.scuba_oxygen_clean)
        self.assertEqual(asset.scuba_oxygen_clean_date, date(2025, 2, 1))

    def test_lifecycle_not_changed_by_scuba_service(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.cyl_cat.id,
                "lifecycle_state": "active",
                "in_service_date": "2024-01-01",
            }
        )
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.vip.id,
                "service_date": date(2025, 1, 1),
                "result": "failed",
            }
        )
        record.action_complete()
        self.assertEqual(asset.lifecycle_state, "active")
