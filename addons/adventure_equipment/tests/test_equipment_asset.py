# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAdventureEquipmentAsset(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.Product = cls.env["product.product"]
        cls.partner = cls.env["res.partner"].create({"name": "Equipment Test Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")

    def _create_asset(self, **vals):
        defaults = {
            "partner_id": self.partner.id,
            "category_id": self.category.id,
        }
        defaults.update(vals)
        return self.Asset.create(defaults)

    def test_create_without_product(self):
        asset = self._create_asset(
            brand_name="Apeks",
            model_name="XTX50",
            acquisition_source="other_shop",
            lifecycle_state="draft",
        )
        self.assertFalse(asset.product_id)
        self.assertEqual(asset.acquisition_source, "other_shop")
        self.assertTrue(asset.name and asset.name != "New")

    def test_create_with_product_and_serial(self):
        product = self.Product.create(
            {
                "name": "Test Regulator",
                "default_code": "TEST-REG-01",
                "barcode": "1234567890123",
            }
        )
        asset = self._create_asset(
            product_id=product.id,
            serial_number="SN-TEST-001",
            acquisition_source="shop_sale",
            lifecycle_state="draft",
        )
        self.assertEqual(asset.product_id, product)
        self.assertEqual(asset.product_tmpl_id, product.product_tmpl_id)
        self.assertEqual(asset.serial_number, "SN-TEST-001")
        self.assertTrue(asset.sold_by_this_shop)
        serial_ids = asset.identifier_ids.filtered(
            lambda row: row.id_type == "serial" and row.primary
        )
        self.assertEqual(len(serial_ids), 1)
        self.assertEqual(serial_ids.name, "SN-TEST-001")

    def test_product_defaults_fill_blanks(self):
        product = self.Product.create(
            {
                "name": "Catalog Regulator",
                "default_code": "CAT-REG-99",
                "barcode": "9876543210987",
            }
        )
        asset = self._create_asset(product_id=product.id)
        self.assertEqual(asset.model_name, "Catalog Regulator")
        self.assertEqual(asset.manufacturer_sku, "CAT-REG-99")
        self.assertEqual(asset.barcode, "9876543210987")
        self.assertEqual(asset.snapshot_product_name, product.display_name)
        self.assertEqual(asset.snapshot_model, "Catalog Regulator")
        self.assertEqual(asset.snapshot_sku, "CAT-REG-99")

    def test_refresh_product_defaults_overwrites(self):
        product = self.Product.create(
            {
                "name": "Refresh Product",
                "default_code": "REF-001",
            }
        )
        asset = self._create_asset(
            product_id=product.id,
            brand_name="Manual Brand",
            model_name="Manual Model",
            manufacturer_sku="OLD-SKU",
        )
        product.write({"default_code": "REF-UPDATED", "name": "Refresh Product Updated"})
        # product.product name write updates template in Odoo for single-variant
        asset.action_refresh_product_defaults()
        self.assertEqual(asset.model_name, product.product_tmpl_id.name)
        self.assertEqual(asset.manufacturer_sku, "REF-UPDATED")
        self.assertEqual(asset.snapshot_sku, "REF-UPDATED")
        self.assertEqual(asset.snapshot_model, product.product_tmpl_id.name)
        self.assertNotEqual(asset.model_name, "Manual Model")

    def test_product_archive_does_not_archive_equipment(self):
        product = self.Product.create({"name": "Archivable Product"})
        asset = self._create_asset(
            product_id=product.id,
            lifecycle_state="active",
            in_service_date="2026-01-01",
        )
        product.active = False
        self.assertTrue(asset.active)
        self.assertEqual(asset.product_id, product)
        self.assertEqual(asset.lifecycle_state, "active")

    def test_product_unlink_preserves_snapshots(self):
        product = self.Product.create(
            {
                "name": "Disposable Product",
                "default_code": "DISPOSE-01",
            }
        )
        asset = self._create_asset(product_id=product.id)
        snapshot_name = asset.snapshot_product_name
        snapshot_model = asset.snapshot_model
        product.unlink()
        asset.invalidate_recordset()
        self.assertFalse(asset.product_id)
        self.assertFalse(asset.product_tmpl_id)
        self.assertEqual(asset.snapshot_product_name, snapshot_name)
        self.assertEqual(asset.snapshot_model, snapshot_model)

    def test_product_variant_template_consistency_validation(self):
        product_a = self.Product.create({"name": "Product A"})
        product_b = self.Product.create({"name": "Product B"})
        with self.assertRaises(ValidationError):
            self._create_asset(
                product_id=product_a.id,
                product_tmpl_id=product_b.product_tmpl_id.id,
            )

    def test_lifecycle_transitions(self):
        asset = self._create_asset(lifecycle_state="draft")
        asset.write({"lifecycle_state": "active", "in_service_date": "2026-01-01"})
        self.assertEqual(asset.lifecycle_state, "active")
        asset.write({"lifecycle_state": "in_service"})
        self.assertEqual(asset.lifecycle_state, "in_service")
        asset.write({"lifecycle_state": "active"})
        with self.assertRaises(UserError):
            asset.write({"lifecycle_state": "draft"})

    def test_retire_preserves_history(self):
        asset = self._create_asset(
            lifecycle_state="active",
            in_service_date="2026-01-01",
        )
        ownership_count = len(asset.ownership_ids)
        event_count = len(asset.event_ids)
        asset.action_retire()
        self.assertEqual(asset.lifecycle_state, "retired")
        self.assertTrue(asset.retired_on)
        self.assertEqual(len(asset.ownership_ids), ownership_count)
        self.assertGreater(len(asset.event_ids), event_count)

    def test_unlink_draft_ok(self):
        asset = self._create_asset(lifecycle_state="draft")
        asset_id = asset.id
        asset.unlink()
        self.assertFalse(self.Asset.browse(asset_id).exists())

    def test_unlink_active_blocked(self):
        asset = self._create_asset(
            lifecycle_state="active",
            in_service_date="2026-01-01",
        )
        with self.assertRaises(UserError):
            asset.unlink()

    def test_serial_duplicate_validation(self):
        self._create_asset(
            brand_name="Scubapro",
            model_name="MK25",
            serial_number="DUP-SN-001",
            lifecycle_state="draft",
        )
        with self.assertRaises(ValidationError):
            self._create_asset(
                brand_name="Scubapro",
                model_name="MK25",
                serial_number="dup-sn-001",
                lifecycle_state="draft",
            )
