# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestAdventureWaiverUpsert(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Waiver = cls.env["adventure.waiver"]
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
            }
        )

    def test_upsert_creates_and_matches(self):
        record = self.Waiver.upsert_provider_waiver(
            "manual",
            "abc123",
            {
                "title": "Demo Waiver",
                "email": "ada@example.com",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "participant_payload": [{"firstName": "Ada"}],
            },
        )
        self.assertEqual(record.provider, "manual")
        self.assertEqual(record.external_id, "abc123")
        self.assertEqual(record.match_state, "matched")
        self.assertEqual(record.partner_id, self.partner)

    def test_upsert_idempotent_per_provider(self):
        first = self.Waiver.upsert_provider_waiver(
            "manual",
            "same-id",
            {"title": "One", "email": "ada@example.com"},
        )
        second = self.Waiver.upsert_provider_waiver(
            "manual",
            "same-id",
            {"title": "Two", "email": "ada@example.com"},
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.title, "Two")
        self.assertEqual(
            self.Waiver.search_count(
                [("provider", "=", "manual"), ("external_id", "=", "same-id")]
            ),
            1,
        )
