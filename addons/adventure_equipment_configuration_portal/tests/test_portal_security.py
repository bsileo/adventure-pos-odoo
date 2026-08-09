# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEquipmentConfigurationPortalSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env["adventure.equipment.category"]
        cls.category = Category.create({"name": "Config Portal Category"})
        cls.partner_a = cls.env["res.partner"].create(
            {"name": "List Owner A", "email": "list_a@example.test"}
        )
        cls.partner_b = cls.env["res.partner"].create(
            {"name": "List Owner B", "email": "list_b@example.test"}
        )
        portal_group = cls.env.ref("base.group_portal")
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        cls.user_a = Users.create(
            {
                "name": "Portal List A",
                "login": "portal_list_a@example.test",
                "partner_id": cls.partner_a.id,
                "group_ids": [(6, 0, [portal_group.id])],
            }
        )
        cls.user_b = Users.create(
            {
                "name": "Portal List B",
                "login": "portal_list_b@example.test",
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
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )
        cls.asset_b = Asset.create(
            {
                "partner_id": cls.partner_b.id,
                "category_id": cls.category.id,
                "nickname": "B Reg",
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )
        Config = cls.env["adventure.equipment.configuration"]
        cls.list_a = Config.create(
            {
                "name": "A packing",
                "partner_id": cls.partner_a.id,
                "list_kind": "packing",
            }
        )
        cls.list_b = Config.create(
            {
                "name": "B configuration",
                "partner_id": cls.partner_b.id,
                "list_kind": "configuration",
            }
        )

    def test_portal_sees_only_own_lists(self):
        Config = self.env["adventure.equipment.configuration"]
        own = Config.with_user(self.user_a).search([])
        self.assertIn(self.list_a, own)
        self.assertNotIn(self.list_b, own)

    def test_portal_cannot_read_other_list(self):
        with self.assertRaises(AccessError):
            self.list_b.with_user(self.user_a).read(["name"])

    def test_portal_can_create_and_delete_own_list(self):
        Config = self.env["adventure.equipment.configuration"].with_user(self.user_a)
        record = Config.create(
            {
                "name": "New list",
                "partner_id": self.partner_a.id,
                "list_kind": "configuration",
                "company_id": self.env.company.id,
            }
        )
        Line = self.env["adventure.equipment.configuration.line"].with_user(self.user_a)
        Line.create(
            {
                "configuration_id": record.id,
                "line_type": "asset",
                "asset_id": self.asset_a.id,
            }
        )
        record.unlink()
        self.assertFalse(record.exists())

    def test_portal_cannot_attach_other_asset(self):
        Line = self.env["adventure.equipment.configuration.line"].with_user(self.user_a)
        from odoo.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Line.create(
                {
                    "configuration_id": self.list_a.id,
                    "line_type": "asset",
                    "asset_id": self.asset_b.id,
                }
            )
