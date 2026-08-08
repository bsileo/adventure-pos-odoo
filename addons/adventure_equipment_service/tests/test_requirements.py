# -*- coding: utf-8 -*-

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAdventureEquipmentServiceRequirements(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Req Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.post_impact = cls.env.ref(
            "adventure_equipment_service.service_type_post_impact_inspection"
        )
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.Policy = cls.env["adventure.equipment.service.policy"]
        cls.Requirement = cls.env["adventure.equipment.service.requirement"]
        cls.Type = cls.env["adventure.equipment.service.type"]
        # Isolate from demo/data policies loaded with the module.
        cls.Policy.search([]).write({"active": False})
        # Dedicated type avoids collisions with demo Annual Inspection policies.
        cls.annual = cls.Type.create(
            {
                "name": "Test Annual Inspection",
                "code": "TEST_ANNUAL",
                "classification": "inspection",
                "default_warning_lead_days": 30,
                "default_grace_days": 14,
            }
        )
        cls.cert = cls.Type.create(
            {
                "name": "Test Safety Certification",
                "code": "TEST_CERT",
                "classification": "certification",
            }
        )
        cls.policy = cls.Policy.create(
            {
                "name": "Annual Regulators",
                "service_type_id": cls.annual.id,
                "category_id": cls.category.id,
                "interval_quantity": 12,
                "interval_unit": "months",
                "warning_lead_days": 30,
                "grace_days": 14,
                "first_due_basis": "in_service_date",
                "priority": 100,
            }
        )

    def _asset(self, **vals):
        defaults = {
            "partner_id": self.partner.id,
            "category_id": self.category.id,
            "lifecycle_state": "active",
            "in_service_date": "2025-09-15",
        }
        defaults.update(vals)
        return self.Asset.create(defaults)

    def test_generation_idempotent_and_policy_change(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        reqs = self.Requirement.search(
            [("asset_id", "=", asset.id), ("is_policy_managed", "=", True)]
        )
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs.next_due_date, date(2026, 9, 15))
        first_id = reqs.id

        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        reqs2 = self.Requirement.search(
            [("asset_id", "=", asset.id), ("is_policy_managed", "=", True), ("active", "=", True)]
        )
        self.assertEqual(len(reqs2), 1)
        self.assertEqual(reqs2.id, first_id)

        self.policy.write({"interval_quantity": 24})
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        reqs2.invalidate_recordset()
        self.assertEqual(reqs2.next_due_date, date(2027, 9, 15))

    def test_manual_one_time_and_coexistence(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset)
        manual = self.Requirement.create(
            {
                "name": "Post impact",
                "asset_id": asset.id,
                "company_id": asset.company_id.id,
                "service_type_id": self.post_impact.id,
                "source_classification": "manual",
                "is_policy_managed": False,
                "is_one_time": True,
                "is_recurring": False,
                "next_due_date": "2026-04-01",
                "manual_reason": "Dropped on boat deck",
                "forecast_confidence": "confirmed",
            }
        )
        self.Requirement.sync_asset_requirements(asset)
        active = self.Requirement.search(
            [("asset_id", "=", asset.id), ("active", "=", True)]
        )
        self.assertEqual(len(active), 2)
        self.assertIn(manual, active)

    def test_override_survives_recalc_and_restore(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        req = asset.service_requirement_ids[:1]
        req.write(
            {
                "override_active": True,
                "override_next_due_date": date(2026, 12, 1),
                "override_reason": "Customer traveling",
                "override_user_id": self.env.user.id,
                "override_date": "2026-01-02 10:00:00",
                "next_due_date": date(2026, 12, 1),
                "schedule_source": "override",
            }
        )
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 3))
        self.assertEqual(req.next_due_date, date(2026, 12, 1))
        self.assertTrue(req.override_active)
        req.action_restore_policy_schedule()
        self.assertFalse(req.override_active)
        self.assertEqual(req.next_due_date, date(2026, 9, 15))

    def test_waiver_expiration_reactivates(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        req = asset.service_requirement_ids[:1]
        req.write(
            {
                "waived": True,
                "waiver_reason": "Temporary",
                "waiver_expiration_date": date(2026, 2, 1),
            }
        )
        req._recompute_status(today=date(2026, 1, 15))
        self.assertEqual(req.status, "waived")
        req._expire_temporary_states(today=date(2026, 2, 2))
        req._recompute_status(today=date(2026, 2, 2))
        self.assertFalse(req.waived)
        self.assertNotEqual(req.status, "waived")

    def test_status_aging_on_requirement(self):
        asset = self._asset(in_service_date="2025-09-15")
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        req = asset.service_requirement_ids[:1]
        req._recompute_status(today=date(2026, 8, 1))
        self.assertEqual(req.status, "current")
        req._recompute_status(today=date(2026, 8, 20))
        self.assertEqual(req.status, "due_soon")
        req._recompute_status(today=date(2026, 9, 15))
        self.assertEqual(req.status, "due")
        req._recompute_status(today=date(2026, 10, 1))
        self.assertEqual(req.status, "overdue")

    def test_policy_deactivation_suspends_policy_requirement(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset)
        req = asset.service_requirement_ids.filtered(
            lambda row: row.is_policy_managed and row.service_type_id == self.annual
        )
        self.assertTrue(req)
        self.policy.active = False
        self.Requirement.sync_asset_requirements(asset)
        self.assertFalse(req.active)
        self.assertTrue(req.suspended)

    def test_second_service_type_coexists(self):
        asset = self._asset()
        self.Policy.create(
            {
                "name": "Cert policy",
                "service_type_id": self.cert.id,
                "category_id": self.category.id,
                "interval_quantity": 24,
                "interval_unit": "months",
            }
        )
        self.Requirement.sync_asset_requirements(asset)
        types = asset.service_requirement_ids.mapped("service_type_id")
        self.assertEqual(len(types), 2)
