# -*- coding: utf-8 -*-

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAdventureEquipmentScubaPolicies(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Scuba Policy Customer"})
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.Policy = cls.env["adventure.equipment.service.policy"]
        cls.Requirement = cls.env["adventure.equipment.service.requirement"]
        cls.cyl_cat = cls.env.ref("adventure_equipment.equipment_category_cylinder")
        cls.reg_cat = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.vip = cls.env.ref("adventure_equipment_scuba.service_type_cylinder_vip")
        cls.hydro = cls.env.ref("adventure_equipment_scuba.service_type_hydrostatic_test")
        cls.reg_svc = cls.env.ref("adventure_equipment_scuba.service_type_regulator_service")

    def test_scuba_service_types_exist(self):
        for xmlid in (
            "service_type_cylinder_vip",
            "service_type_hydrostatic_test",
            "service_type_regulator_service",
            "service_type_bcd_service",
            "service_type_oxygen_clean",
            "service_type_drysuit_leak_test",
            "service_type_dive_computer_service",
        ):
            rec = self.env.ref("adventure_equipment_scuba.%s" % xmlid)
            self.assertTrue(rec.active)

    def test_cylinder_gets_vip_and_hydro_requirements(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.cyl_cat.id,
                "lifecycle_state": "active",
                "in_service_date": "2024-06-01",
                "scuba_cylinder_material": "aluminum",
            }
        )
        winners = self.Policy.select_winning_policies(asset)
        types = winners.mapped("service_type_id")
        self.assertIn(self.vip, types)
        self.assertIn(self.hydro, types)

        self.Requirement.sync_asset_requirements(asset, on_date=date(2025, 1, 1))
        req_types = asset.service_requirement_ids.filtered("active").mapped(
            "service_type_id"
        )
        self.assertIn(self.vip, req_types)
        self.assertIn(self.hydro, req_types)

        vip_req = asset.service_requirement_ids.filtered(
            lambda row: row.service_type_id == self.vip and row.active
        )
        hydro_req = asset.service_requirement_ids.filtered(
            lambda row: row.service_type_id == self.hydro and row.active
        )
        self.assertEqual(vip_req.next_due_date, date(2025, 6, 1))
        self.assertEqual(hydro_req.next_due_date, date(2029, 6, 1))

    def test_regulator_gets_annual_service_policy(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.reg_cat.id,
                "lifecycle_state": "active",
                "in_service_date": "2024-06-01",
            }
        )
        winners = self.Policy.select_winning_policies(asset)
        self.assertIn(self.reg_svc, winners.mapped("service_type_id"))
        self.Requirement.sync_asset_requirements(asset, on_date=date(2025, 1, 1))
        req = asset.service_requirement_ids.filtered(
            lambda row: row.service_type_id == self.reg_svc and row.active
        )
        self.assertEqual(len(req), 1)
        self.assertEqual(req.next_due_date, date(2025, 6, 1))

    def test_sync_idempotent_for_cylinder(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.cyl_cat.id,
                "lifecycle_state": "active",
                "in_service_date": "2024-06-01",
            }
        )
        self.Requirement.sync_asset_requirements(asset)
        self.Requirement.sync_asset_requirements(asset)
        vip_reqs = asset.service_requirement_ids.filtered(
            lambda row: row.service_type_id == self.vip and row.active
        )
        hydro_reqs = asset.service_requirement_ids.filtered(
            lambda row: row.service_type_id == self.hydro and row.active
        )
        self.assertEqual(len(vip_reqs), 1)
        self.assertEqual(len(hydro_reqs), 1)
