# -*- coding: utf-8 -*-

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.adventure_equipment_service.models.service_date_utils import (
    add_interval,
    compute_requirement_status,
    compute_schedule_dates,
)


@tagged("post_install", "-at_install")
class TestAdventureEquipmentServiceDates(TransactionCase):
    def test_month_and_year_intervals_calendar_aware(self):
        self.assertEqual(add_interval(date(2024, 1, 31), 1, "months"), date(2024, 2, 29))
        self.assertEqual(add_interval(date(2024, 2, 29), 1, "years"), date(2025, 2, 28))
        self.assertEqual(add_interval(date(2026, 3, 15), 12, "months"), date(2027, 3, 15))
        self.assertNotEqual(add_interval(date(2026, 3, 15), 12, "months"), date(2027, 3, 14))

    def test_warning_grace_and_status_aging(self):
        warning, due, grace = compute_schedule_dates(
            date(2026, 9, 15), warning_lead_days=30, grace_days=14
        )
        self.assertEqual(warning, date(2026, 8, 16))
        self.assertEqual(due, date(2026, 9, 15))
        self.assertEqual(grace, date(2026, 9, 29))

        self.assertEqual(
            compute_requirement_status(
                today=date(2026, 8, 1), due_date=due, warning_date=warning, grace_date=grace
            ),
            "current",
        )
        self.assertEqual(
            compute_requirement_status(
                today=date(2026, 8, 16), due_date=due, warning_date=warning, grace_date=grace
            ),
            "due_soon",
        )
        self.assertEqual(
            compute_requirement_status(
                today=date(2026, 9, 15), due_date=due, warning_date=warning, grace_date=grace
            ),
            "due",
        )
        self.assertEqual(
            compute_requirement_status(
                today=date(2026, 9, 29), due_date=due, warning_date=warning, grace_date=grace
            ),
            "due",
        )
        self.assertEqual(
            compute_requirement_status(
                today=date(2026, 9, 30), due_date=due, warning_date=warning, grace_date=grace
            ),
            "overdue",
        )

    def test_no_grace_overdue_after_due_date(self):
        warning, due, grace = compute_schedule_dates(
            date(2026, 5, 1), warning_lead_days=7, grace_days=0
        )
        self.assertFalse(grace)
        self.assertEqual(
            compute_requirement_status(
                today=date(2026, 5, 1), due_date=due, warning_date=warning, grace_date=grace
            ),
            "due",
        )
        self.assertEqual(
            compute_requirement_status(
                today=date(2026, 5, 2), due_date=due, warning_date=warning, grace_date=grace
            ),
            "overdue",
        )
