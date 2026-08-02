# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestSmartwaiverMatching(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Waiver = cls.env["smartwaiver.waiver"]
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Kyle Smith",
                "email": "kyle@example.com",
            }
        )

    def test_email_match_single(self):
        waiver = self.Waiver.create(
            {
                "waiver_id": "w-email-1",
                "email": "Kyle@Example.com",
                "email_normalized": "kyle@example.com",
                "first_name": "Kyle",
                "last_name": "Smith",
            }
        )
        waiver._apply_auto_match()
        self.assertEqual(waiver.match_state, "matched")
        self.assertEqual(waiver.match_method, "email")
        self.assertEqual(waiver.partner_id, self.partner)

    def test_email_ambiguous(self):
        self.env["res.partner"].create(
            {
                "name": "Kyle Other",
                "email": "kyle@example.com",
            }
        )
        waiver = self.Waiver.create(
            {
                "waiver_id": "w-email-2",
                "email": "kyle@example.com",
                "email_normalized": "kyle@example.com",
            }
        )
        waiver._apply_auto_match()
        self.assertEqual(waiver.match_state, "ambiguous")
        self.assertFalse(waiver.partner_id)

    def test_unmatched_no_partner_create(self):
        before = self.env["res.partner"].search_count([])
        waiver = self.Waiver.create(
            {
                "waiver_id": "w-unmatched-1",
                "email": "nobody@example.com",
                "email_normalized": "nobody@example.com",
                "first_name": "Nobody",
                "last_name": "Here",
            }
        )
        waiver._apply_auto_match()
        self.assertEqual(waiver.match_state, "unmatched")
        self.assertFalse(waiver.partner_id)
        after = self.env["res.partner"].search_count([])
        self.assertEqual(before, after)

    def test_rematch_when_partner_created(self):
        waiver = self.Waiver.create(
            {
                "waiver_id": "w-later-1",
                "email": "later@example.com",
                "email_normalized": "later@example.com",
                "first_name": "Later",
                "last_name": "Guest",
            }
        )
        waiver._apply_auto_match()
        self.assertEqual(waiver.match_state, "unmatched")
        partner = self.env["res.partner"].create(
            {
                "name": "Later Guest",
                "email": "later@example.com",
            }
        )
        self.assertEqual(waiver.match_state, "matched")
        self.assertEqual(waiver.partner_id, partner)

    def test_name_match_single(self):
        waiver = self.Waiver.create(
            {
                "waiver_id": "w-name-1",
                "first_name": "Kyle",
                "last_name": "Smith",
                "name_normalized": "kyle smith",
            }
        )
        waiver._apply_auto_match()
        self.assertEqual(waiver.match_state, "matched")
        self.assertEqual(waiver.match_method, "name")
        self.assertEqual(waiver.partner_id, self.partner)

    def test_manual_link_preserved(self):
        other = self.env["res.partner"].create({"name": "Other Person"})
        waiver = self.Waiver.create(
            {
                "waiver_id": "w-manual-1",
                "email": "kyle@example.com",
                "email_normalized": "kyle@example.com",
                "partner_id": other.id,
                "match_state": "manual",
                "match_method": "manual",
            }
        )
        waiver._apply_auto_match()
        self.assertEqual(waiver.match_state, "manual")
        self.assertEqual(waiver.partner_id, other)
