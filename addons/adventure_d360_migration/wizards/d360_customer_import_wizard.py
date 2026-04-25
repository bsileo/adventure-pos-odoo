# -*- coding: utf-8 -*-

import base64
import csv
import hashlib
import io
from collections import Counter
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError


class AdventureD360CustomerImportWizard(models.TransientModel):
    _name = "adventure.d360.customer.import.wizard"
    _description = "Upload and preprocess a D360 customer export"

    data_file = fields.Binary(string="Customer CSV", required=True)
    filename = fields.Char(string="Filename")
    shop_name = fields.Char(
        string="Shop",
        help="Optional label for the shop or tenant that produced the export.",
    )
    upload_notes = fields.Text(
        string="How the export was obtained",
        help="Use this to capture the D360 menu path, export operator, or timing notes.",
    )
    delimiter = fields.Char(
        size=1,
        default=",",
        help="CSV delimiter. The D360 contact export is expected to be comma-separated.",
    )
    encoding = fields.Char(
        default="utf-8-sig",
        help="Text encoding. utf-8-sig handles common Excel UTF-8 exports with a BOM.",
    )

    def _normalize_header_map(self, fieldnames):
        return {((field or "").strip().lower()): field for field in fieldnames if field is not None}

    def _require_header(self, header_map, header_name):
        key = (header_name or "").strip().lower()
        actual = header_map.get(key)
        if not actual:
            raise UserError(
                _("The uploaded file is missing the required header '%s'.") % header_name
            )
        return actual

    def _parse_iso_or_us_date(self, raw_value):
        value = (raw_value or "").strip()
        if not value or value == "0000-00-00":
            return False
        for fmt in ("%Y-%m-%d", "%m-%d-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return False

    def _parse_yes_no(self, raw_value):
        return (raw_value or "").strip().upper() == "YES"

    def _prepare_line_values(self, row, row_number, header_map):
        def get(header_name):
            actual = header_map.get(header_name.strip().lower())
            return (row.get(actual) or "") if actual else ""

        values = {
            "sequence": row_number * 10,
            "source_customer_id": (get("Customer ID") or "").strip(),
            "mailing_name": get("Mailing Name").strip(),
            "address_line_0": get("Address Line 0").strip(),
            "address_line_1": get("Address Line 1").strip(),
            "city": get("City").strip(),
            "state_name": get("State").strip(),
            "zip_code": get("Zip Code").strip(),
            "country_name": get("Country").strip(),
            "last_name": get("Last Name").strip(),
            "first_name": get("First Name").strip(),
            "middle_initial": get("Middle Initial").strip(),
            "gender": get("Gender").strip(),
            "email": get("Email Address").strip(),
            "home_phone": get("Home Phone").strip(),
            "work_phone": get("Work Phone").strip(),
            "mobile_phone": get("Cellular Phone Number").strip(),
            "primary_mailing_list": self._parse_yes_no(get("Primary Mailing List Flag")),
            "birthday": self._parse_iso_or_us_date(get("Birthday")),
            "customer_type": get("Customer Type").strip(),
            "invoice_type": get("Invoice Type").strip(),
            "last_purchase_date": self._parse_iso_or_us_date(get("Last Purchase Date")),
            "import_state": "pending",
        }
        if not values["source_customer_id"]:
            raise UserError(
                _("Row %(row)s is missing Customer ID, which is required for D360 upserts.")
                % {"row": row_number}
            )
        return values

    def action_upload_and_preprocess(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please upload a CSV file."))

        raw = base64.b64decode(self.data_file)
        encoding = (self.encoding or "utf-8-sig").strip() or "utf-8-sig"
        delimiter = (self.delimiter or ",")[:1] or ","
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError as exc:
            raise UserError(
                _("Could not decode the CSV as %(encoding)s: %(error)s")
                % {"encoding": encoding, "error": exc}
            ) from exc

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            raise UserError(_("The uploaded CSV does not contain a header row."))

        header_map = self._normalize_header_map(reader.fieldnames)
        for required_header in (
            "Customer ID",
            "Last Name",
            "First Name",
            "Email Address",
            "Primary Mailing List Flag",
        ):
            self._require_header(header_map, required_header)

        Line = self.env["adventure.d360.customer.import.line"]
        parsed_rows = []
        for row_number, row in enumerate(reader, start=1):
            values = self._prepare_line_values(row, row_number, header_map)
            values.update(Line.classify_source_values(values))
            parsed_rows.append(values)

        if not parsed_rows:
            raise UserError(_("No data rows were found in the uploaded file."))

        id_counts = Counter(row["source_customer_id"] for row in parsed_rows)
        for values in parsed_rows:
            if id_counts[values["source_customer_id"]] > 1:
                reason = values.get("classification_reasons") or ""
                if reason:
                    reason += "; "
                values["classification_reasons"] = (
                    reason + _("Duplicate Customer ID appears more than once in this file")
                )
                values["review_needed"] = True
                if values.get("classification_confidence") == "high":
                    values["classification_confidence"] = "medium"

        display_name = (self.shop_name or self.filename or _("D360 customer import")).strip()
        if display_name.lower().endswith(".csv"):
            display_name = display_name[:-4].strip() or _("D360 customer import")

        Batch = self.env["adventure.d360.customer.import.batch"]
        batch = Batch.create(
            {
                "name": display_name,
                "shop_name": self.shop_name,
                "source_filename": self.filename or _("upload.csv"),
                "source_checksum": hashlib.sha256(raw).hexdigest(),
                "source_encoding": encoding,
                "source_delimiter": delimiter,
                "upload_notes": self.upload_notes,
                "state": "review",
            }
        )
        for values in parsed_rows:
            values["batch_id"] = batch.id
        Line.create(parsed_rows)

        return {
            "type": "ir.actions.act_window",
            "name": _("D360 customer import"),
            "res_model": "adventure.d360.customer.import.batch",
            "res_id": batch.id,
            "view_mode": "form",
            "target": "current",
        }
