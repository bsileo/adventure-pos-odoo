# -*- coding: utf-8 -*-

import base64
import hashlib

from odoo import _, fields, models
from odoo.exceptions import UserError


class AdventureD360HistoryImportWizard(models.TransientModel):
    _name = "adventure.d360.history.import.wizard"
    _description = "Upload D360 historical transaction XLSX"

    data_file = fields.Binary(string="Transaction report (XLSX)", required=True)
    filename = fields.Char(string="Filename")
    upload_notes = fields.Text(
        string="Import notes",
        help="Optional: export path, operator, or date range for audit.",
    )
    dedupe_mode = fields.Selection(
        [
            ("keep_all", "Keep all rows (default)"),
            ("collapse_identical", "Collapse consecutive identical lines per invoice"),
        ],
        default="keep_all",
        required=True,
    )

    def action_upload_and_preview(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please upload an XLSX file."))
        raw = base64.b64decode(self.data_file)
        if not raw:
            raise UserError(_("The uploaded file is empty."))

        display = (self.filename or _("D360 history import")).strip()
        if display.lower().endswith(".xlsx"):
            display = display[:-5].strip() or _("D360 history import")

        Batch = self.env["adventure.d360.history.import.batch"]
        batch = Batch.create(
            {
                "name": display,
                "source_file": self.data_file,
                "source_filename": self.filename or "upload.xlsx",
                "source_checksum": hashlib.sha256(raw).hexdigest(),
                "dedupe_mode": self.dedupe_mode,
                "upload_notes": self.upload_notes,
            }
        )
        batch.action_analyze()
        return {
            "type": "ir.actions.act_window",
            "name": _("Historical import"),
            "res_model": "adventure.d360.history.import.batch",
            "res_id": batch.id,
            "view_mode": "form",
            "target": "current",
        }
