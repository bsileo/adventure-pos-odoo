# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


SAMPLE_PAYLOAD = {
    "waiverId": "abc123waiver",
    "templateId": "tpl001",
    "title": "Demo Waiver",
    "createdOn": "2017-01-24 13:12:29",
    "expirationDate": "",
    "expired": False,
    "verified": True,
    "kiosk": True,
    "firstName": "Ada",
    "middleName": "",
    "lastName": "Lovelace",
    "email": "ada@example.com",
    "participants": [
        {
            "firstName": "Ada",
            "lastName": "Lovelace",
            "isMinor": False,
        }
    ],
    "customWaiverFields": {
        "field1": {"value": "Friend", "displayText": "How did you hear?"},
    },
    "tags": ["Green Team"],
}


class TestSmartwaiverProviderUpsert(TransactionCase):
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

    def test_upsert_creates_provider_row(self):
        record = self.Waiver._smartwaiver_upsert_from_payload(SAMPLE_PAYLOAD)
        self.assertTrue(record)
        self.assertEqual(record.provider, "smartwaiver")
        self.assertEqual(record.external_id, "abc123waiver")
        self.assertEqual(record.title, "Demo Waiver")
        self.assertEqual(record.match_state, "matched")
        self.assertEqual(record.partner_id, self.partner)

    def test_upsert_idempotent(self):
        first = self.Waiver._smartwaiver_upsert_from_payload(SAMPLE_PAYLOAD)
        second = self.Waiver._smartwaiver_upsert_from_payload(
            dict(SAMPLE_PAYLOAD, title="Demo Waiver Updated")
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.title, "Demo Waiver Updated")

    def test_template_allowlist_skips(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "adventure_smartwaiver.template_ids",
            "other-template",
        )
        record = self.Waiver._smartwaiver_upsert_from_payload(SAMPLE_PAYLOAD)
        self.assertFalse(record)
