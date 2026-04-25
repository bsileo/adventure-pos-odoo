from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.adventure_d360_migration.models.d360_customer_import import (
    AdventureD360CustomerImportLine,
)


class TestD360CustomerImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Batch = cls.env["adventure.d360.customer.import.batch"]
        cls.Line = cls.env["adventure.d360.customer.import.line"]

    def _create_batch(self, line_count=0):
        batch = self.Batch.create(
            {
                "name": "Test import batch",
                "state": "review",
                "source_filename": "contacts.csv",
                "source_checksum": "abc123",
                "source_encoding": "utf-8-sig",
                "source_delimiter": ",",
            }
        )
        for index in range(1, line_count + 1):
            self._create_line(batch, customer_id=f"CUST-{index}", sequence=index * 10)
        return batch

    def _create_line(self, batch, customer_id, sequence):
        return self.Line.create(
            {
                "batch_id": batch.id,
                "sequence": sequence,
                "source_customer_id": customer_id,
                "first_name": "Ada",
                "last_name": f"Customer {sequence}",
                "email": f"{customer_id.lower()}@example.com",
                "partner_kind_guess": "person",
                "classification_confidence": "high",
                "review_needed": False,
            }
        )

    def test_chunked_upsert_reports_progress(self):
        batch = self._create_batch(line_count=5)

        first_result = batch.action_upsert_partners_chunk(chunk_size=2)
        batch.invalidate_recordset()
        self.assertFalse(first_result["done"])
        self.assertEqual(first_result["batch_values"]["processed_count"], 2)
        self.assertEqual(first_result["batch_values"]["imported_count"], 2)
        self.assertEqual(first_result["batch_values"]["failed_count"], 0)
        self.assertEqual(first_result["batch_values"]["progress_percent"], 40.0)
        self.assertEqual(batch.state, "review")

        second_result = batch.action_upsert_partners_chunk(chunk_size=2)
        self.assertFalse(second_result["done"])
        self.assertEqual(second_result["batch_values"]["processed_count"], 4)
        self.assertEqual(second_result["batch_values"]["progress_percent"], 80.0)

        final_result = batch.action_upsert_partners_chunk(chunk_size=2)
        batch.invalidate_recordset()
        self.assertTrue(final_result["done"])
        self.assertEqual(final_result["batch_values"]["processed_count"], 5)
        self.assertEqual(final_result["batch_values"]["imported_count"], 5)
        self.assertEqual(final_result["batch_values"]["failed_count"], 0)
        self.assertEqual(final_result["batch_values"]["progress_percent"], 100.0)
        self.assertEqual(batch.state, "done")

    def test_failed_row_does_not_abort_remaining_rows(self):
        batch = self._create_batch()
        good_line_a = self._create_line(batch, customer_id="GOOD-1", sequence=10)
        failed_line = self._create_line(batch, customer_id="FAIL-1", sequence=20)
        good_line_b = self._create_line(batch, customer_id="GOOD-2", sequence=30)

        original_prepare_partner_vals = AdventureD360CustomerImportLine.prepare_partner_vals

        def prepare_partner_vals_with_failure(line):
            line.ensure_one()
            if line.source_customer_id == "FAIL-1":
                raise UserError("Simulated partner upsert failure")
            return original_prepare_partner_vals(line)

        with patch.object(
            AdventureD360CustomerImportLine,
            "prepare_partner_vals",
            autospec=True,
            side_effect=prepare_partner_vals_with_failure,
        ):
            result = batch.action_upsert_partners_chunk(chunk_size=10)

        batch.invalidate_recordset()
        good_line_a.invalidate_recordset()
        failed_line.invalidate_recordset()
        good_line_b.invalidate_recordset()

        self.assertTrue(result["done"])
        self.assertEqual(batch.imported_count, 2)
        self.assertEqual(batch.failed_count, 1)
        self.assertEqual(batch.processed_count, 3)
        self.assertEqual(batch.progress_percent, 100.0)
        self.assertEqual(batch.state, "done")
        self.assertEqual(good_line_a.import_state, "imported")
        self.assertEqual(good_line_b.import_state, "imported")
        self.assertEqual(failed_line.import_state, "failed")
        self.assertIn("Simulated partner upsert failure", failed_line.import_error)

    def test_ambiguous_rows_stay_pending_until_resolved(self):
        batch = self._create_batch()
        imported_line = self._create_line(batch, customer_id="GOOD-1", sequence=10)
        ambiguous_line = self._create_line(batch, customer_id="AMB-1", sequence=20)
        ambiguous_line.write(
            {
                "partner_kind_guess": "ambiguous",
                "classification_confidence": "low",
                "review_needed": True,
            }
        )

        result = batch.action_upsert_partners_chunk(chunk_size=10)

        batch.invalidate_recordset()
        imported_line.invalidate_recordset()
        ambiguous_line.invalidate_recordset()

        self.assertTrue(result["done"])
        self.assertFalse(result["batch_done"])
        self.assertEqual(batch.state, "review")
        self.assertEqual(batch.imported_count, 1)
        self.assertEqual(batch.processed_count, 1)
        self.assertEqual(batch.line_count, 2)
        self.assertEqual(batch.pending_count, 1)
        self.assertEqual(imported_line.import_state, "imported")
        self.assertEqual(ambiguous_line.import_state, "pending")

    def test_pending_count_tracks_pending_import_state(self):
        batch = self._create_batch()
        pending_line = self._create_line(batch, customer_id="PEND-1", sequence=10)
        imported_line = self._create_line(batch, customer_id="DONE-1", sequence=20)
        failed_line = self._create_line(batch, customer_id="FAIL-1", sequence=30)

        imported_line.write({"import_state": "imported"})
        failed_line.write({"import_state": "failed", "import_error": "simulated"})
        batch.invalidate_recordset()

        self.assertEqual(batch.line_count, 3)
        self.assertEqual(batch.pending_count, 1)
        self.assertEqual(batch.imported_count, 1)
        self.assertEqual(batch.failed_count, 1)
        self.assertEqual(batch.processed_count, 2)
        self.assertEqual(batch.pending_line_ids.ids, pending_line.ids)
