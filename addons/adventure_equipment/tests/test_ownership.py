# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAdventureEquipmentOwnership(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.Ownership = cls.env["adventure.equipment.ownership"]
        cls.Wizard = cls.env["adventure.equipment.ownership.transfer.wizard"]
        cls.partner_a = cls.env["res.partner"].create({"name": "Owner A"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Owner B"})
        cls.parent_company = cls.env["res.partner"].create(
            {
                "name": "Dive Club LLC",
                "is_company": True,
            }
        )
        cls.child_contact = cls.env["res.partner"].create(
            {
                "name": "Member Contact",
                "parent_id": cls.parent_company.id,
                "type": "contact",
            }
        )
        cls.category = cls.env.ref("adventure_equipment.equipment_category_bcd")

    def _create_asset(self, partner=None, **vals):
        defaults = {
            "partner_id": (partner or self.partner_a).id,
            "category_id": self.category.id,
            "lifecycle_state": "draft",
        }
        defaults.update(vals)
        return self.Asset.create(defaults)

    def test_initial_ownership_on_create(self):
        asset = self._create_asset()
        current = asset.ownership_ids.filtered("is_current")
        self.assertEqual(len(current), 1)
        self.assertEqual(current.partner_id, self.partner_a)
        self.assertEqual(current.change_type, "registration")
        self.assertTrue(current.date_from)

    def test_transfer_wizard(self):
        asset = self._create_asset(
            lifecycle_state="active",
            in_service_date="2026-01-01",
        )
        wizard = self.Wizard.create(
            {
                "asset_id": asset.id,
                "from_partner_id": self.partner_a.id,
                "to_partner_id": self.partner_b.id,
                "transfer_date": "2026-06-15",
                "reason": "sale",
                "verification_state": "verified",
                "notes": "Sold to diver B",
            }
        )
        wizard.action_confirm()
        self.assertEqual(asset.partner_id, self.partner_b)
        current = asset.ownership_ids.filtered("is_current")
        self.assertEqual(len(current), 1)
        self.assertEqual(current.partner_id, self.partner_b)
        self.assertEqual(current.change_type, "sale")
        previous = asset.ownership_ids.filtered(lambda row: not row.is_current)
        self.assertEqual(len(previous), 1)
        self.assertEqual(previous.partner_id, self.partner_a)
        self.assertEqual(previous.date_to, wizard.transfer_date)

    def test_overlapping_current_ownership_prevented(self):
        asset = self._create_asset()
        current = asset.ownership_ids.filtered("is_current")
        with self.assertRaises(ValidationError):
            self.Ownership.create(
                {
                    "asset_id": asset.id,
                    "partner_id": self.partner_b.id,
                    "date_from": "2026-01-01",
                    "change_type": "transfer",
                    "is_current": True,
                }
            )
        self.assertEqual(len(asset.ownership_ids.filtered("is_current")), 1)
        self.assertEqual(current, asset.ownership_ids.filtered("is_current"))

    def test_partner_equipment_asset_count_contact_only(self):
        self._create_asset(
            partner=self.child_contact,
            brand_name="Mares",
            model_name="Rover",
            lifecycle_state="active",
            in_service_date="2026-01-01",
        )
        self.assertEqual(self.child_contact.equipment_asset_count, 1)
        self.assertEqual(self.parent_company.equipment_asset_count, 0)
