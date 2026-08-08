# -*- coding: utf-8 -*-

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAdventureEquipmentServiceRecords(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Service Rec Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.post_impact = cls.env.ref(
            "adventure_equipment_service.service_type_post_impact_inspection"
        )
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.Policy = cls.env["adventure.equipment.service.policy"]
        cls.Requirement = cls.env["adventure.equipment.service.requirement"]
        cls.Record = cls.env["adventure.equipment.service.record"]
        cls.annual = cls.env["adventure.equipment.service.type"].create(
            {
                "name": "Record Test Annual",
                "code": "REC_ANNUAL",
                "classification": "inspection",
                "requires_result": True,
            }
        )
        cls.policy = cls.Policy.create(
            {
                "name": "Annual",
                "service_type_id": cls.annual.id,
                "category_id": cls.category.id,
                "interval_quantity": 12,
                "interval_unit": "months",
                "warning_lead_days": 30,
                "grace_days": 14,
                "priority": 100,
            }
        )

    def _asset(self):
        return self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.category.id,
                "lifecycle_state": "active",
                "in_service_date": "2025-01-01",
            }
        )

    def test_completion_advances_schedule_and_rollup(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset, on_date=date(2025, 2, 1))
        req = asset.service_requirement_ids[:1]
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.annual.id,
                "requirement_id": req.id,
                "service_date": date(2026, 1, 10),
                "result": "passed",
                "summary": "Annual done",
            }
        )
        record.action_complete()
        self.assertEqual(record.state, "completed")
        self.assertEqual(req.last_completed_date, date(2026, 1, 10))
        self.assertEqual(req.next_due_date, date(2027, 1, 10))
        asset.invalidate_recordset()
        self.assertIn(asset.service_status, ("current", "due_soon", "due", "unknown"))
        # Lifecycle unchanged
        self.assertEqual(asset.lifecycle_state, "active")

    def test_explicit_next_recommended_date_precedence(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset)
        req = asset.service_requirement_ids[:1]
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.annual.id,
                "requirement_id": req.id,
                "service_date": date(2026, 3, 1),
                "result": "passed",
                "next_recommended_date": date(2026, 8, 1),
            }
        )
        record.action_complete()
        self.assertEqual(req.next_due_date, date(2026, 8, 1))
        self.assertTrue(req.next_recommended_from_record)
        self.assertEqual(req.schedule_source, "service_record")

    def test_one_time_completion_does_not_recur(self):
        asset = self._asset()
        req = self.Requirement.create(
            {
                "name": "Impact",
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.post_impact.id,
                "source_classification": "manual",
                "is_policy_managed": False,
                "is_one_time": True,
                "next_due_date": date(2026, 4, 1),
            }
        )
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.post_impact.id,
                "requirement_id": req.id,
                "service_date": date(2026, 4, 2),
                "result": "passed",
            }
        )
        record.action_complete()
        self.assertEqual(req.status, "completed")
        self.assertFalse(req.next_due_date)

    def test_verified_protection_and_void_correction(self):
        asset = self._asset()
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.annual.id,
                "service_date": date(2026, 1, 1),
                "result": "passed",
            }
        )
        record.action_complete()
        record.action_verify()
        with self.assertRaises(UserError):
            record.write({"findings": "rewrite history"})
        record.void_reason = "Typo in date"
        record.action_void()
        self.assertEqual(record.state, "voided")
        replacement = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.annual.id,
                "service_date": date(2026, 1, 2),
                "result": "passed",
            }
        )
        self.assertTrue(replacement.id)
        self.assertEqual(record.state, "voided")

    def test_external_unverified_then_verify(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset)
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.annual.id,
                "service_date": date(2026, 2, 1),
                "result": "passed",
                "performed_by_this_shop": False,
                "external_provider_name": "Other Dive Co",
                "verification_state": "unverified",
                "data_provenance": "external",
                "customer_reported": True,
            }
        )
        record.action_complete()
        self.assertEqual(record.verification_state, "unverified")
        record.action_verify()
        self.assertEqual(record.state, "verified")
        self.assertEqual(record.verification_state, "verified")

    def test_policy_change_does_not_rewrite_history(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset)
        req = asset.service_requirement_ids[:1]
        record = self.Record.create(
            {
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.annual.id,
                "requirement_id": req.id,
                "service_date": date(2026, 1, 1),
                "result": "passed",
                "findings": "Original findings",
            }
        )
        record.action_complete()
        original_date = record.service_date
        self.policy.interval_quantity = 24
        self.Requirement.sync_asset_requirements(asset)
        record.invalidate_recordset()
        self.assertEqual(record.service_date, original_date)
        self.assertEqual(record.findings, "Original findings")
        self.assertEqual(record.state, "completed")
