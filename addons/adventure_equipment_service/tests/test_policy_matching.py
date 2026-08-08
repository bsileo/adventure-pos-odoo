# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAdventureEquipmentServicePolicyMatching(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.Policy = cls.env["adventure.equipment.service.policy"]
        cls.Type = cls.env["adventure.equipment.service.type"]
        cls.partner = cls.Partner.create({"name": "Policy Match Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.other_category = cls.env.ref("adventure_equipment.equipment_category_bcd")
        cls.annual = cls.env.ref(
            "adventure_equipment_service.service_type_annual_inspection"
        )
        cls.cert = cls.env.ref(
            "adventure_equipment_service.service_type_safety_certification"
        )
        cls.tag = cls.env["adventure.equipment.tag"].create({"name": "Service Tag"})
        cls.product = cls.env["product.product"].create({"name": "Policy Product"})

    def _asset(self, **vals):
        defaults = {
            "partner_id": self.partner.id,
            "category_id": self.category.id,
            "lifecycle_state": "active",
            "in_service_date": "2026-01-01",
        }
        defaults.update(vals)
        return self.Asset.create(defaults)

    def _policy(self, **vals):
        defaults = {
            "name": "Policy",
            "service_type_id": self.annual.id,
            "company_id": self.env.company.id,
            "interval_quantity": 12,
            "interval_unit": "months",
        }
        defaults.update(vals)
        return self.Policy.create(defaults)

    def test_category_product_tag_brand_default_matching(self):
        asset = self._asset(
            brand_name="Acme",
            model_name="Pro",
            product_id=self.product.id,
            tag_ids=[(6, 0, [self.tag.id])],
        )
        cat = self._policy(name="Cat", category_id=self.category.id, priority=1)
        prod = self._policy(
            name="Prod", product_id=self.product.id, priority=1, sequence=5
        )
        tag = self._policy(name="Tag", tag_id=self.tag.id, priority=1)
        brand = self._policy(
            name="BrandModel", brand_name="Acme", model_name="Pro", priority=1
        )
        default = self._policy(name="Default", is_default=True, priority=1)
        inactive = self._policy(
            name="Inactive", category_id=self.category.id, active=False
        )
        future = self._policy(
            name="Future",
            category_id=self.category.id,
            date_effective="2099-01-01",
        )
        expired = self._policy(
            name="Expired",
            category_id=self.category.id,
            date_expiration="2020-01-01",
        )
        applicable = self.Policy.find_applicable_policies(asset, on_date="2026-06-01")
        self.assertIn(cat, applicable)
        self.assertIn(prod, applicable)
        self.assertIn(tag, applicable)
        self.assertIn(brand, applicable)
        self.assertIn(default, applicable)
        self.assertNotIn(inactive, applicable)
        self.assertNotIn(future, applicable)
        self.assertNotIn(expired, applicable)

        winners = self.Policy.select_winning_policies(asset, on_date="2026-06-01")
        self.assertEqual(winners, prod)

    def test_product_beats_category_and_default_fallback(self):
        asset = self._asset()
        self._policy(name="Cat", category_id=self.category.id, priority=50)
        self._policy(name="Default", is_default=True, priority=99)
        winners = self.Policy.select_winning_policies(asset)
        self.assertEqual(winners.name, "Cat")

        bare = self._asset(category_id=self.other_category.id)
        winners = self.Policy.select_winning_policies(bare)
        self.assertEqual(winners.name, "Default")

    def test_multiple_independent_service_types(self):
        asset = self._asset()
        p1 = self._policy(name="Annual", service_type_id=self.annual.id)
        p2 = self._policy(name="Cert", service_type_id=self.cert.id, is_default=True)
        winners = self.Policy.select_winning_policies(asset)
        self.assertEqual(set(winners.ids), {p1.id, p2.id})

    def test_company_mismatch_ignored(self):
        other = self.env["res.company"].create({"name": "Other Co Service"})
        asset = self._asset()
        foreign = self._policy(
            name="Foreign",
            company_id=other.id,
            is_default=True,
        )
        applicable = self.Policy.find_applicable_policies(asset)
        self.assertNotIn(foreign, applicable)
