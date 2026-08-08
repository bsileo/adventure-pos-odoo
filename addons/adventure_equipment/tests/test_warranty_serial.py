# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAdventureEquipmentWarrantySerial(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.partner = cls.env["res.partner"].create({"name": "Warranty Serial Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")

    def _create_asset(self, **vals):
        defaults = {
            "partner_id": self.partner.id,
            "category_id": self.category.id,
            "lifecycle_state": "draft",
        }
        defaults.update(vals)
        return self.Asset.create(defaults)

    def test_warranty_not_registered(self):
        asset = self._create_asset(warranty_registered=False)
        self.assertEqual(asset.warranty_status, "not_registered")

    def test_warranty_active(self):
        today = self.Asset._fields["warranty_end_date"].today(self)
        asset = self._create_asset(
            warranty_registered=True,
            warranty_end_date=today + timedelta(days=90),
        )
        self.assertEqual(asset.warranty_status, "active")

    def test_warranty_expired(self):
        today = self.Asset._fields["warranty_end_date"].today(self)
        asset = self._create_asset(
            warranty_registered=True,
            warranty_end_date=today - timedelta(days=1),
        )
        self.assertEqual(asset.warranty_status, "expired")

    def test_warranty_lifetime(self):
        asset = self._create_asset(warranty_lifetime=True)
        self.assertEqual(asset.warranty_status, "lifetime")

    def test_warranty_not_applicable(self):
        asset = self._create_asset(warranty_not_applicable=True)
        self.assertEqual(asset.warranty_status, "not_applicable")

    def test_warranty_start_after_end_raises(self):
        with self.assertRaises(ValidationError):
            self._create_asset(
                warranty_registered=True,
                warranty_start_date="2026-06-01",
                warranty_end_date="2026-01-01",
            )

    def test_serial_same_brand_model_blocked(self):
        self._create_asset(
            brand_name="Scubapro",
            model_name="MK25",
            serial_number="DUP-SN-WS-001",
        )
        with self.assertRaises(ValidationError):
            self._create_asset(
                brand_name="Scubapro",
                model_name="MK25",
                serial_number="dup-sn-ws-001",
            )

    def test_serial_same_serial_different_brand_allowed(self):
        self._create_asset(
            brand_name="Scubapro",
            model_name="MK25",
            serial_number="SHARED-SN-001",
        )
        asset_b = self._create_asset(
            brand_name="Apeks",
            model_name="MK25",
            serial_number="SHARED-SN-001",
        )
        self.assertEqual(asset_b.serial_number, "SHARED-SN-001")

    def test_serial_duplicate_allowed_with_context(self):
        self._create_asset(
            brand_name="Mares",
            model_name="Rover",
            serial_number="CTX-SN-001",
        )
        asset_dup = self.Asset.with_context(
            equipment_allow_duplicate_serial=True
        ).create(
            {
                "partner_id": self.partner.id,
                "category_id": self.category.id,
                "brand_name": "Mares",
                "model_name": "Rover",
                "serial_number": "CTX-SN-001",
                "lifecycle_state": "draft",
            }
        )
        self.assertEqual(asset_dup.serial_number, "CTX-SN-001")
