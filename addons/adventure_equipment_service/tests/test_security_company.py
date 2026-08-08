# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAdventureEquipmentServiceSecurityCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Sec Customer"})
        cls.category = cls.env.ref("adventure_equipment.equipment_category_regulator")
        cls.env["adventure.equipment.service.policy"].search([]).write({"active": False})
        cls.annual = cls.env["adventure.equipment.service.type"].create(
            {
                "name": "Security Test Annual",
                "code": "SEC_ANNUAL",
                "classification": "inspection",
            }
        )
        cls.asset = cls.env["adventure.equipment.asset"].create(
            {
                "partner_id": cls.partner.id,
                "category_id": cls.category.id,
                "lifecycle_state": "active",
                "in_service_date": "2025-01-01",
            }
        )
        cls.policy = cls.env["adventure.equipment.service.policy"].create(
            {
                "name": "Sec Policy",
                "service_type_id": cls.annual.id,
                "category_id": cls.category.id,
                "interval_quantity": 12,
                "interval_unit": "months",
                "priority": 100,
            }
        )
        cls.env["adventure.equipment.service.requirement"].sync_asset_requirements(
            cls.asset
        )
        cls.requirement = cls.asset.service_requirement_ids[:1]

        cls.viewer = cls.env["res.users"].create(
            {
                "name": "Eq Viewer",
                "login": "eq_service_viewer",
                "email": "eq_service_viewer@example.com",
                "company_id": cls.env.company.id,
                "company_ids": [(6, 0, [cls.env.company.id])],
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("adventure_equipment.group_equipment_viewer").id,
                        ],
                    )
                ],
            }
        )
        cls.user = cls.env["res.users"].create(
            {
                "name": "Eq User",
                "login": "eq_service_user",
                "email": "eq_service_user@example.com",
                "company_id": cls.env.company.id,
                "company_ids": [(6, 0, [cls.env.company.id])],
                "group_ids": [
                    (
                        6,
                        0,
                        [cls.env.ref("adventure_equipment.group_equipment_user").id],
                    )
                ],
            }
        )
        cls.manager = cls.env["res.users"].create(
            {
                "name": "Eq Manager",
                "login": "eq_service_manager",
                "email": "eq_service_manager@example.com",
                "company_id": cls.env.company.id,
                "company_ids": [(6, 0, [cls.env.company.id])],
                "group_ids": [
                    (
                        6,
                        0,
                        [cls.env.ref("adventure_equipment.group_equipment_manager").id],
                    )
                ],
            }
        )

    def test_viewer_can_read_not_write_policy(self):
        req = self.requirement.with_user(self.viewer)
        self.assertEqual(req.service_type_id, self.annual)
        with self.assertRaises(AccessError):
            self.policy.with_user(self.viewer).write({"name": "Nope"})

    def test_user_can_create_draft_record_manager_configures_policy(self):
        record = (
            self.env["adventure.equipment.service.record"]
            .with_user(self.user)
            .create(
                {
                    "asset_id": self.asset.id,
                    "company_id": self.asset.company_id.id,
                    "service_type_id": self.annual.id,
                    "service_date": "2026-01-01",
                    "result": "passed",
                }
            )
        )
        self.assertEqual(record.state, "draft")
        self.policy.with_user(self.manager).write({"grace_days": 7})
        self.assertEqual(self.policy.grace_days, 7)

    def test_cross_company_requirement_blocked(self):
        other = self.env["res.company"].create({"name": "Other Shop"})
        with self.assertRaises(ValidationError):
            self.env["adventure.equipment.service.requirement"].create(
                {
                    "name": "Bad company",
                    "asset_id": self.asset.id,
                    "company_id": other.id,
                    "service_type_id": self.annual.id,
                    "source_classification": "manual",
                    "is_policy_managed": False,
                    "next_due_date": "2026-01-01",
                }
            )

    def test_attachment_follows_record_acl(self):
        record = self.env["adventure.equipment.service.record"].create(
            {
                "asset_id": self.asset.id,
                "company_id": self.asset.company_id.id,
                "service_type_id": self.annual.id,
                "service_date": "2026-01-01",
                "result": "passed",
                "internal_notes": "secret tech note",
            }
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": "report.pdf",
                "res_model": "adventure.equipment.service.record",
                "res_id": record.id,
                "datas": "c2VjcmV0",
            }
        )
        # Viewer can read the record and linked attachment metadata through ACL.
        self.assertTrue(record.with_user(self.viewer).name)
        self.assertTrue(attachment.with_user(self.viewer).name)
        with self.assertRaises(AccessError):
            record.with_user(self.viewer).write({"summary": "nope"})
