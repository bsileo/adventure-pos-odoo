# -*- coding: utf-8 -*-

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.adventure_equipment_service.models.service_date_utils import (
    rollup_asset_service_status,
)


@tagged("post_install", "-at_install")
class TestAdventureEquipmentServiceCronRollup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Cron Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.annual = cls.env.ref(
            "adventure_equipment_service.service_type_annual_inspection"
        )
        cls.Requirement = cls.env["adventure.equipment.service.requirement"]
        cls.Policy = cls.env["adventure.equipment.service.policy"]
        cls.Asset = cls.env["adventure.equipment.asset"]
        cls.policy = cls.Policy.create(
            {
                "name": "Cron Annual",
                "service_type_id": cls.annual.id,
                "category_id": cls.category.id,
                "interval_quantity": 12,
                "interval_unit": "months",
                "warning_lead_days": 30,
                "grace_days": 14,
            }
        )

    def _asset(self, in_service_date="2025-09-15"):
        return self.Asset.create(
            {
                "partner_id": self.partner.id,
                "category_id": self.category.id,
                "lifecycle_state": "active",
                "in_service_date": in_service_date,
            }
        )

    def test_rollup_severity_and_waived_ignored(self):
        self.assertEqual(rollup_asset_service_status([]), "not_applicable")
        self.assertEqual(rollup_asset_service_status(["current"]), "current")
        self.assertEqual(
            rollup_asset_service_status(["current", "due_soon", "overdue"]), "overdue"
        )
        self.assertEqual(
            rollup_asset_service_status(["waived", "suspended", "completed"]),
            "not_applicable",
        )
        self.assertEqual(
            rollup_asset_service_status(["waived", "due"]),
            "due",
        )

    def test_asset_rollup_mixed_statuses(self):
        asset = self._asset()
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        req = asset.service_requirement_ids[:1]
        req._recompute_status(today=date(2026, 10, 1))
        asset._recompute_service_rollup()
        self.assertEqual(asset.service_status, "overdue")
        self.assertEqual(asset.service_overdue_count, 1)

        req.write(
            {
                "waived": True,
                "waiver_reason": "ignore for rollup",
            }
        )
        req._recompute_status(today=date(2026, 10, 1))
        asset._recompute_service_rollup()
        self.assertEqual(asset.service_status, "not_applicable")

    def test_cron_idempotent_no_duplicates(self):
        assets = self.Asset
        for idx in range(3):
            assets |= self._asset(in_service_date="2025-01-0%s" % (idx + 1))
        self.env["ir.config_parameter"].sudo().set_param(
            "adventure_equipment_service.cron_last_asset_id", "0"
        )
        self.Requirement.cron_process_equipment_service(batch_size=2)
        self.Requirement.cron_process_equipment_service(batch_size=2)
        self.Requirement.cron_process_equipment_service(batch_size=2)
        for asset in assets:
            managed = asset.service_requirement_ids.filtered(
                lambda row: row.is_policy_managed and row.active
            )
            self.assertEqual(len(managed), 1)

    def test_partner_contact_only_counts(self):
        parent = self.env["res.partner"].create(
            {"name": "Parent Co", "is_company": True}
        )
        child = self.env["res.partner"].create(
            {"name": "Child Contact", "parent_id": parent.id}
        )
        asset = self.Asset.create(
            {
                "partner_id": child.id,
                "category_id": self.category.id,
                "lifecycle_state": "active",
                "in_service_date": "2025-09-15",
            }
        )
        self.Requirement.sync_asset_requirements(asset, on_date=date(2026, 1, 1))
        req = asset.service_requirement_ids[:1]
        req._recompute_status(today=date(2026, 10, 1))
        asset._recompute_service_rollup()
        child.invalidate_recordset()
        parent.invalidate_recordset()
        self.assertEqual(child.equipment_service_overdue_count, 1)
        self.assertEqual(parent.equipment_service_overdue_count, 0)
