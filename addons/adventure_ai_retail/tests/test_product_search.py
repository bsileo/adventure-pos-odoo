# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestAdventureProductSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        category = cls.env["product.category"].create({"name": "Wetsuits"})
        pos_categ = cls.env["pos.category"].create({"name": "Wetsuits"})
        cls.wetsuit = cls.env["product.template"].create(
            {
                "name": "Men's 7mm Semi-Dry Wetsuit L",
                "default_code": "WS-7MM-L",
                "list_price": 349.0,
                "sale_ok": True,
                "available_in_pos": True,
                "categ_id": category.id,
                "pos_categ_ids": [(6, 0, [pos_categ.id])],
                "type": "consu",
            }
        )
        cls.bcd = cls.env["product.template"].create(
            {
                "name": "Travel BCD Compact",
                "default_code": "BCD-TRAVEL",
                "list_price": 429.0,
                "sale_ok": True,
                "available_in_pos": True,
                "type": "consu",
            }
        )
        cls.hidden = cls.env["product.template"].create(
            {
                "name": "Backoffice Only 7mm Suit",
                "list_price": 10.0,
                "sale_ok": True,
                "available_in_pos": False,
                "type": "consu",
            }
        )

    def test_search_ranks_wetsuit_query(self):
        result = self.env["adventure.product_search"].search_products(
            query="men's 7mm semi-dry size L",
            limit=10,
            available_in_pos_only=True,
        )
        self.assertGreaterEqual(result["count"], 1)
        top = result["products"][0]
        self.assertEqual(top["product_tmpl_id"], self.wetsuit.id)
        self.assertTrue(top["score"] > 0)

    def test_search_excludes_non_pos_when_requested(self):
        result = self.env["adventure.product_search"].search_products(
            query="7mm",
            available_in_pos_only=True,
        )
        ids = {row["product_tmpl_id"] for row in result["products"]}
        self.assertIn(self.wetsuit.id, ids)
        self.assertNotIn(self.hidden.id, ids)

    def test_capability_search_products_registered(self):
        from odoo.addons.adventure_ai.services import capability_registry as caps

        capability = caps.get_capability("search_products")
        self.assertTrue(capability)
        self.assertEqual(capability.feature, "pos_retail")
        ai_user = self.env["res.users"].create(
            {
                "name": "Retail AI User",
                "login": "retail_ai_user",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("adventure_ai.group_user").id,
                        ],
                    )
                ],
            }
        )
        self.env["ir.config_parameter"].sudo().set_param("adventure_ai.provider", "mock")
        result = (
            self.env["adventure.ai.orchestrator"]
            .with_user(ai_user)
            .run_turn(
                "7mm semi-dry",
                profile="pos_retail",
                channel="pos",
                context={"feature": "pos_retail"},
            )
        )
        self.assertTrue(any(p["product_tmpl_id"] == self.wetsuit.id for p in result["products"]))
