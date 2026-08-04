# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAdventureEquipmentSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.viewer_group = cls.env.ref("adventure_equipment.group_equipment_viewer")
        cls.manager_group = cls.env.ref("adventure_equipment.group_equipment_manager")
        cls.partner = cls.env["res.partner"].create({"name": "Security Test Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_other")

    def test_manager_group_exists(self):
        self.assertTrue(self.manager_group)
        self.assertEqual(self.manager_group.name, "Manager")
        self.assertIn(self.viewer_group, self.manager_group.implied_ids)

    def test_viewer_can_read_equipment(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.category.id,
                "brand_name": "Test Brand",
                "model_name": "Test Model",
                "lifecycle_state": "draft",
            }
        )
        viewer_user = self.env["res.users"].create(
            {
                "name": "Equipment Viewer Test",
                "login": "equipment_viewer_test",
                "company_id": self.env.company.id,
                "company_ids": [(6, 0, [self.env.company.id])],
                "groups_id": [(6, 0, [self.viewer_group.id])],
            }
        )
        read_data = self.Asset.with_user(viewer_user).browse(asset.id).read(["name"])
        self.assertEqual(len(read_data), 1)
        self.assertEqual(read_data[0]["id"], asset.id)
