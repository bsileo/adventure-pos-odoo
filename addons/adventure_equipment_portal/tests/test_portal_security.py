# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEquipmentPortalSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env["adventure.equipment.category"]
        cls.category = Category.create({"name": "Portal Test Category"})
        cls.partner_a = cls.env["res.partner"].create(
            {"name": "Portal Owner A", "email": "owner_a@example.test"}
        )
        cls.partner_b = cls.env["res.partner"].create(
            {"name": "Portal Owner B", "email": "owner_b@example.test"}
        )
        portal_group = cls.env.ref("base.group_portal")
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        cls.user_a = Users.create(
            {
                "name": "Portal A",
                "login": "portal_a_equip@example.test",
                "partner_id": cls.partner_a.id,
                "group_ids": [(6, 0, [portal_group.id])],
            }
        )
        cls.user_b = Users.create(
            {
                "name": "Portal B",
                "login": "portal_b_equip@example.test",
                "partner_id": cls.partner_b.id,
                "group_ids": [(6, 0, [portal_group.id])],
            }
        )
        Asset = cls.env["adventure.equipment.asset"]
        cls.asset_a = Asset.create(
            {
                "partner_id": cls.partner_a.id,
                "category_id": cls.category.id,
                "nickname": "A Reg",
                "brand_name": "BrandA",
                "model_name": "ModelA",
                "serial_number": "PORTAL-A-001",
                "acquisition_source": "shop_sale",
                "ownership_verification_state": "verified",
                "lifecycle_state": "active",
            }
        )
        cls.asset_b = Asset.create(
            {
                "partner_id": cls.partner_b.id,
                "category_id": cls.category.id,
                "nickname": "B Comp",
                "brand_name": "BrandB",
                "model_name": "ModelB",
                "serial_number": "PORTAL-B-001",
                "acquisition_source": "shop_sale",
                "ownership_verification_state": "verified",
                "lifecycle_state": "active",
            }
        )

    def test_portal_user_sees_only_own_equipment(self):
        Asset = self.env["adventure.equipment.asset"]
        own = Asset.with_user(self.user_a).search([])
        self.assertIn(self.asset_a, own)
        self.assertNotIn(self.asset_b, own)

    def test_portal_user_cannot_read_other_equipment(self):
        with self.assertRaises(AccessError):
            self.asset_b.with_user(self.user_a).read(["nickname"])

    def test_portal_user_can_update_own_nickname(self):
        self.asset_a.with_user(self.user_a).write({"nickname": "Updated Nick"})
        self.assertEqual(self.asset_a.nickname, "Updated Nick")

    def test_portal_user_can_register_equipment(self):
        Asset = self.env["adventure.equipment.asset"].with_user(self.user_a)
        asset = Asset.create(
            {
                "partner_id": self.partner_a.id,
                "category_id": self.category.id,
                "nickname": "New Tank",
                "brand_name": "Catalina",
                "serial_number": "PORTAL-NEW-001",
                "acquisition_source": "customer_reported",
                "ownership_verification_state": "pending",
                "lifecycle_state": "draft",
            }
        )
        self.assertEqual(asset.partner_id, self.partner_a)
        self.assertEqual(asset.acquisition_source, "customer_reported")
        # Sequence numbering must work for portal (ir.sequence is staff-ACL'd).
        self.assertTrue(asset.name)
        self.assertNotEqual(asset.name, "New")
        self.assertTrue(asset.ownership_ids)
        self.assertTrue(asset.event_ids)
