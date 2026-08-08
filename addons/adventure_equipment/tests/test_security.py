# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAdventureEquipmentSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.viewer_group = cls.env.ref("adventure_equipment.group_equipment_viewer")
        cls.user_group = cls.env.ref("adventure_equipment.group_equipment_user")
        cls.manager_group = cls.env.ref("adventure_equipment.group_equipment_manager")
        cls.internal_user = cls.env.ref("base.group_user")
        cls.partner = cls.env["res.partner"].create({"name": "Security Test Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_other")

    def _make_user(self, name, login, groups):
        return self.env["res.users"].create(
            {
                "name": name,
                "login": login,
                "company_id": self.env.company.id,
                "company_ids": [(6, 0, [self.env.company.id])],
                # Odoo 19 uses group_ids (not groups_id).
                "group_ids": [(6, 0, [g.id for g in groups])],
            }
        )

    def test_manager_group_exists(self):
        self.assertTrue(self.manager_group)
        self.assertEqual(self.manager_group.name, "Manager")
        # Direct imply chain: Manager → User → Viewer
        self.assertIn(self.user_group, self.manager_group.implied_ids)
        self.assertIn(self.viewer_group, self.user_group.implied_ids)
        self.assertIn(self.viewer_group, self.manager_group.all_implied_ids)

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
        viewer_user = self._make_user(
            "Equipment Viewer Test",
            "equipment_viewer_test",
            [self.internal_user, self.viewer_group],
        )
        read_data = self.Asset.with_user(viewer_user).browse(asset.id).read(["name"])
        self.assertEqual(len(read_data), 1)
        self.assertEqual(read_data[0]["id"], asset.id)

    def test_viewer_cannot_write(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.category.id,
                "brand_name": "Test Brand",
                "model_name": "Test Model",
                "lifecycle_state": "draft",
            }
        )
        viewer_user = self._make_user(
            "Equipment Viewer Write Test",
            "equipment_viewer_write_test",
            [self.internal_user, self.viewer_group],
        )
        with self.assertRaises(AccessError):
            asset.with_user(viewer_user).write({"nickname": "Should Fail"})

    def test_user_cannot_unlink_asset(self):
        asset = self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.category.id,
                "brand_name": "Test Brand",
                "model_name": "Test Model",
                "lifecycle_state": "draft",
            }
        )
        equipment_user = self._make_user(
            "Equipment User Unlink Test",
            "equipment_user_unlink_test",
            [self.internal_user, self.user_group],
        )
        with self.assertRaises(AccessError):
            asset.with_user(equipment_user).unlink()
