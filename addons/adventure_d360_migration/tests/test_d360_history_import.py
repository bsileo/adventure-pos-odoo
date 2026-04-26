# -*- coding: utf-8 -*-
"""Automated tests and smoke-test notes for D360 historical archive import.

Smoke test (manual / CI with Odoo shell):

1. ``pip install -r requirements.txt`` (includes openpyxl).
2. Upgrade module: ``odoo -d DB -u adventure_d360_migration --stop-after-init``.
3. Settings → Technical → D360 Migration → New historical import → upload
   ``sample_data/Report_builder_1777175252.xlsx`` → Upload & preview → Import to archive.
4. Confirm archive order count ≈ 366, line count ≈ 1359, and that no ``pos.order`` /
   ``sale.order`` rows were created around the import window (compare counts before/after).

See ``TestD360HistoryImportSampleXlsx`` below for an automated version when the sample file
is present in the repository checkout.
"""

import base64
import os

from odoo.tests.common import TransactionCase


class TestD360HistoryImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Batch = cls.env["adventure.d360.history.import.batch"]

    def _minimal_xlsx_b64(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl is not installed")
        from io import BytesIO

        buf = BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        headers = [
            "Location",
            "Customer ID",
            "First Name",
            "Last Name",
            "Customer Email",
            "Address 1",
            "Address 2",
            "City",
            "State",
            "Zip",
            "Country",
            "Customer phone",
            "Customer type",
            "Invoice type",
            "Invoice number",
            "Date",
            "Part number",
            "Barcode",
            "Description",
            "Serial Number",
            "Category",
            "Vendor",
            "Department",
            "Manufacturer",
            "Taxable",
            "Tax Collected1",
            "Tax Collected2",
            "Tax Collected3",
            "Sales Person",
            "Sold Qty",
            "Unit Price",
            "Ext. price",
            "Delivered Qty",
            "Returned Qty",
            "Date Delivered",
            "Cost",
            "Ext. cost",
            "Margin",
            "Technician",
            "Instructor",
            "Primary Color",
            "Secondary Color",
            "Accent Color",
            "Size",
        ]
        ws.append(headers)
        ws.append(
            [
                "Test Loc",
                "CUST-1",
                "T",
                "User",
                "t.user@example.com",
                "1 Main",
                "",
                "Town",
                "PA",
                "12345",
                "United States",
                "4125550000",
                "Retail",
                "Retail",
                "INV-100",
                "2026-01-15 10:00:00",
                "SKU-1",
                "1234567890123",
                "Test widget",
                "",
                "Cat",
                "Ven",
                "Dept",
                "Mfr",
                "1",
                "0",
                "0",
                "0",
                "Seller",
                "2",
                "10.00",
                "20.00",
                "2",
                "0",
                "2026-01-15 10:00:01",
                "5",
                "10",
                "10",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )
        wb.save(buf)
        return base64.b64encode(buf.getvalue())

    def test_preview_and_import_minimal_xlsx(self):
        raw_b64 = self._minimal_xlsx_b64()
        batch = self.Batch.create(
            {
                "name": "Unit test history",
                "source_file": raw_b64,
                "source_filename": "minimal.xlsx",
                "dedupe_mode": "keep_all",
            }
        )
        batch.action_analyze()
        self.assertEqual(batch.row_count, 1)
        self.assertEqual(batch.invoice_count, 1)
        self.assertEqual(batch.customer_key_count, 1)

        pos_before = self.env["pos.order"].search_count([]) if "pos.order" in self.env else 0
        so_before = self.env["sale.order"].search_count([]) if "sale.order" in self.env else 0
        sm_before = (
            self.env["stock.move"].search_count([]) if "stock.move" in self.env else 0
        )
        am_before = (
            self.env["account.move"].search_count([]) if "account.move" in self.env else 0
        )

        batch.action_import_archive()
        self.assertEqual(batch.state, "imported")

        order = self.env["adventure.history.order"].search(
            [("invoice_number", "=", "INV-100"), ("location", "=", "Test Loc")]
        )
        self.assertEqual(len(order), 1)
        self.assertEqual(len(order.line_ids), 1)
        self.assertEqual(order.line_ids.sold_qty, 2.0)

        if "pos.order" in self.env:
            self.assertEqual(self.env["pos.order"].search_count([]), pos_before)
        if "sale.order" in self.env:
            self.assertEqual(self.env["sale.order"].search_count([]), so_before)
        if "stock.move" in self.env:
            self.assertEqual(self.env["stock.move"].search_count([]), sm_before)
        if "account.move" in self.env:
            self.assertEqual(self.env["account.move"].search_count([]), am_before)

        batch.action_import_archive()
        order.invalidate_recordset()
        self.assertEqual(len(order.line_ids), 1)

    def test_collapse_consecutive_duplicate(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl is not installed")
        from io import BytesIO

        buf = BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        headers = [
            "Location",
            "Customer ID",
            "First Name",
            "Last Name",
            "Customer Email",
            "Address 1",
            "Address 2",
            "City",
            "State",
            "Zip",
            "Country",
            "Customer phone",
            "Customer type",
            "Invoice type",
            "Invoice number",
            "Date",
            "Part number",
            "Barcode",
            "Description",
            "Serial Number",
            "Category",
            "Vendor",
            "Department",
            "Manufacturer",
            "Taxable",
            "Tax Collected1",
            "Tax Collected2",
            "Tax Collected3",
            "Sales Person",
            "Sold Qty",
            "Unit Price",
            "Ext. price",
            "Delivered Qty",
            "Returned Qty",
            "Date Delivered",
            "Cost",
            "Ext. cost",
            "Margin",
            "Technician",
            "Instructor",
            "Primary Color",
            "Secondary Color",
            "Accent Color",
            "Size",
        ]
        ws.append(headers)
        row = [
            "L",
            "C1",
            "A",
            "B",
            "a@b.com",
            "St",
            "",
            "C",
            "S",
            "1",
            "US",
            "",
            "Retail",
            "Retail",
            "I1",
            "2026-01-01 12:00:00",
            "P1",
            "B1",
            "Desc",
            "",
            "",
            "",
            "",
            "",
            "1",
            "0",
            "0",
            "0",
            "",
            "1",
            "1",
            "1",
            "1",
            "0",
            "",
            "0",
            "0",
            "0",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
        ws.append(row)
        ws.append(row)
        wb.save(buf)
        raw_b64 = base64.b64encode(buf.getvalue())

        batch = self.Batch.create(
            {
                "name": "Dedupe test",
                "source_file": raw_b64,
                "source_filename": "dedupe.xlsx",
                "dedupe_mode": "collapse_identical",
            }
        )
        batch.action_import_archive()
        order = self.env["adventure.history.order"].search(
            [("invoice_number", "=", "I1"), ("location", "=", "L")]
        )
        self.assertEqual(len(order.line_ids), 1)
        self.assertEqual(batch.skipped_duplicate_lines, 1)


class TestD360HistoryImportSampleXlsx(TransactionCase):
    """Loads ``sample_data/Report_builder_1777175252.xlsx`` when available (full repo checkout)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Batch = cls.env["adventure.d360.history.import.batch"]

    def test_sample_report_import_shape(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl is not installed")

        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        sample_path = os.path.join(repo_root, "sample_data", "Report_builder_1777175252.xlsx")
        if not os.path.isfile(sample_path):
            self.skipTest("Sample XLSX not in checkout: %s" % sample_path)

        with open(sample_path, "rb") as handle:
            raw_b64 = base64.b64encode(handle.read())

        batch = self.Batch.create(
            {
                "name": "Sample report import test",
                "source_file": raw_b64,
                "source_filename": "Report_builder_1777175252.xlsx",
                "dedupe_mode": "keep_all",
            }
        )
        batch.action_analyze()
        self.assertEqual(batch.skipped_aggregate_rows, 1)
        self.assertEqual(batch.row_count, 1358)
        self.assertEqual(batch.invoice_count, 366)

        pos_before = self.env["pos.order"].search_count([]) if "pos.order" in self.env else 0
        so_before = self.env["sale.order"].search_count([]) if "sale.order" in self.env else 0
        sm_before = (
            self.env["stock.move"].search_count([]) if "stock.move" in self.env else 0
        )
        am_before = (
            self.env["account.move"].search_count([]) if "account.move" in self.env else 0
        )

        batch.action_import_archive()

        if "pos.order" in self.env:
            self.assertEqual(self.env["pos.order"].search_count([]), pos_before)
        if "sale.order" in self.env:
            self.assertEqual(self.env["sale.order"].search_count([]), so_before)
        if "stock.move" in self.env:
            self.assertEqual(self.env["stock.move"].search_count([]), sm_before)
        if "account.move" in self.env:
            self.assertEqual(self.env["account.move"].search_count([]), am_before)

        orders = self.env["adventure.history.order"].search([("import_batch_id", "=", batch.id)])
        self.assertEqual(len(orders), 366)
        self.assertEqual(sum(len(o.line_ids) for o in orders), 1358)
