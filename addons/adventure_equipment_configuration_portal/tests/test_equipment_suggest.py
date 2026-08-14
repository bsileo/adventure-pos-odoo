# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.adventure_equipment_configuration_portal.controllers.equipment_suggest import (
    asset_suggest_domain,
    format_suggest_results,
    match_hint_for_asset,
    rank_suggest_assets,
    tokenize_suggest_query,
)


@tagged("post_install", "-at_install")
class TestEquipmentSuggest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env["adventure.equipment.category"]
        cls.cat_reg = Category.create({"name": "Regulator", "code": "REG"})
        cls.cat_cyl = Category.create({"name": "Cylinder", "code": "CYL"})
        cls.partner = cls.env["res.partner"].create(
            {"name": "Suggest Owner", "email": "suggest_owner@example.test"}
        )
        cls.other = cls.env["res.partner"].create(
            {"name": "Other Owner", "email": "suggest_other@example.test"}
        )
        Asset = cls.env["adventure.equipment.asset"]
        cls.reg = Asset.create(
            {
                "partner_id": cls.partner.id,
                "category_id": cls.cat_reg.id,
                "nickname": "Primary Reg",
                "brand_name": "Scubapro",
                "model_name": "MK25 EVO",
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )
        cls.cyl = Asset.create(
            {
                "partner_id": cls.partner.id,
                "category_id": cls.cat_cyl.id,
                "nickname": "AL80",
                "brand_name": "Luxfer",
                "model_name": "S80",
                "customer_note": "steel alternative sometimes",
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )
        cls.other_reg = Asset.create(
            {
                "partner_id": cls.other.id,
                "category_id": cls.cat_reg.id,
                "nickname": "Someone Else Reg",
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )

    def _search(self, query, exclude_ids=None):
        domain = asset_suggest_domain(self.partner.id, query, exclude_ids=exclude_ids)
        return self.env["adventure.equipment.asset"].search(domain)

    def test_tokenize(self):
        self.assertEqual(tokenize_suggest_query("  Primary   Reg "), ["primary", "reg"])
        self.assertEqual(tokenize_suggest_query("   "), [])

    def test_category_wildcard_regulator(self):
        """Typing the category word finds gear even when nickname lacks it."""
        found = self._search("regulator")
        self.assertIn(self.reg, found)
        self.assertNotIn(self.cyl, found)
        self.assertNotIn(self.other_reg, found)

    def test_multi_token_and(self):
        found = self._search("primary reg")
        self.assertIn(self.reg, found)
        self.assertNotIn(self.cyl, found)

    def test_brand_and_note(self):
        self.assertIn(self.reg, self._search("Scubapro"))
        self.assertIn(self.cyl, self._search("steel"))

    def test_exclude_already_on_list(self):
        found = self._search("reg", exclude_ids=[self.reg.id])
        self.assertNotIn(self.reg, found)

    def test_rank_prefers_category(self):
        # Nickname-only hit vs category hit: category should rank first for "regulator".
        nick_only = self.env["adventure.equipment.asset"].create(
            {
                "partner_id": self.partner.id,
                "category_id": self.cat_cyl.id,
                "nickname": "Backup regulator hose",
                "lifecycle_state": "active",
                "acquisition_source": "manual_shop",
            }
        )
        found = self._search("regulator")
        ranked = rank_suggest_assets(found, "regulator")
        self.assertEqual(ranked[0], self.reg)
        self.assertIn(nick_only, ranked)
        hint = match_hint_for_asset(self.reg, ["regulator"])
        self.assertIn("Category", hint)
        rows = format_suggest_results(ranked, "regulator")
        self.assertEqual(rows[0]["id"], self.reg.id)
        self.assertTrue(rows[0]["match_hint"])
