# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase

from odoo.addons.adventure_ai.services import capability_registry as caps


class TestAdventureAiCapabilityRegistry(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._saved_registry = dict(caps._REGISTRY)
        caps.clear_registry()

        def _echo(env, args, context):
            return {"echo": args.get("text"), "user": env.user.login}

        caps.register_capability(
            caps.Capability(
                name="echo_text",
                description="Echo text for tests",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                handler=_echo,
                risk_class="read",
                feature="test",
                profiles=("default",),
                group_xmlids=("adventure_ai.group_user",),
            )
        )
        cls.ai_user = cls.env["res.users"].create(
            {
                "name": "AI Cashier",
                "login": "ai_cashier_test",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("adventure_ai.group_user").id,
                        ],
                    )
                ],
            }
        )

    @classmethod
    def tearDownClass(cls):
        caps.clear_registry()
        caps._REGISTRY.update(cls._saved_registry)
        super().tearDownClass()

    def test_validate_args_requires_fields(self):
        capability = caps.get_capability("echo_text")
        with self.assertRaises(UserError):
            caps.validate_args(capability, {})

    def test_invoke_as_ai_user(self):
        result = caps.invoke_capability(
            self.env(user=self.ai_user),
            "echo_text",
            {"text": "hello"},
            {},
        )
        self.assertEqual(result["echo"], "hello")
        self.assertEqual(result["user"], "ai_cashier_test")

    def test_invoke_denied_without_group(self):
        plain = self.env["res.users"].create(
            {
                "name": "No AI",
                "login": "no_ai_test",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            caps.invoke_capability(self.env(user=plain), "echo_text", {"text": "x"}, {})


class TestAdventureAiOrchestratorMock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._saved_registry = dict(caps._REGISTRY)
        caps.clear_registry()

        def _search(env, args, context):
            return {
                "query": args.get("query"),
                "products": [
                    {
                        "product_id": 1,
                        "product_tmpl_id": 1,
                        "name": "Mock Wetsuit",
                        "list_price": 10.0,
                        "score": 100,
                    }
                ],
                "count": 1,
            }

        caps.register_capability(
            caps.Capability(
                name="search_products",
                description="Search products",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                handler=_search,
                risk_class="read",
                feature="pos_retail",
                profiles=("pos_retail",),
                group_xmlids=("adventure_ai.group_user",),
            )
        )
        cls.env["ir.config_parameter"].sudo().set_param("adventure_ai.provider", "mock")
        cls.ai_user = cls.env["res.users"].create(
            {
                "name": "AI POS",
                "login": "ai_pos_test",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("adventure_ai.group_user").id,
                        ],
                    )
                ],
            }
        )

    @classmethod
    def tearDownClass(cls):
        caps.clear_registry()
        caps._REGISTRY.update(cls._saved_registry)
        super().tearDownClass()

    def test_run_turn_mock_calls_search_products(self):
        orch = self.env["adventure.ai.orchestrator"].with_user(self.ai_user)
        result = orch.run_turn(
            "men's 7mm semi-dry",
            profile="pos_retail",
            channel="pos",
            context={"feature": "pos_retail"},
        )
        self.assertTrue(result["session_id"])
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["name"], "Mock Wetsuit")
        usage = self.env["adventure.ai.usage"].sudo().search(
            [("session_id", "=", result["session_id"])], limit=1
        )
        self.assertTrue(usage)
        self.assertEqual(usage.feature, "pos_retail")
        self.assertTrue(usage.success)
        self.assertEqual(usage.capability_name, "search_products")
