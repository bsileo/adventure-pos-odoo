# -*- coding: utf-8 -*-

import base64
import csv
import io
import logging
from collections import Counter
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AdventureVendorCategoryMapping(models.Model):
    """One row per unique vendor category string within a batch.

    Lets the user review and correct category suggestions in bulk — one choice
    covers every product that shares the same vendor category label.
    """

    _name = "adventure.vendor.category.mapping"
    _description = "Vendor category mapping"
    _order = "needs_review desc, vendor_category"

    batch_id = fields.Many2one(
        "adventure.vendor.catalog.import.batch",
        string="Batch",
        required=True,
        ondelete="cascade",
    )
    vendor_category = fields.Char(string="Vendor category", readonly=True)
    categ_id = fields.Many2one(
        "product.category",
        string="Product category",
        help="Select the correct Odoo category for all products with this vendor label.",
    )
    match_confidence = fields.Float(
        string="Confidence",
        digits=(16, 2),
        readonly=True,
    )
    needs_review = fields.Boolean(string="Review needed", readonly=True)
    product_count = fields.Integer(string="Products", readonly=True)


class AdventureVendorCatalogImportBatch(models.Model):
    _name = "adventure.vendor.catalog.import.batch"
    _description = "Vendor catalog import batch"
    _order = "id desc"

    name = fields.Char(string="Description", required=True)
    state = fields.Selection(
        [
            ("review", "Review"),
            ("done", "Imported"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="review",
        required=True,
    )
    source_filename = fields.Char(string="Source file")
    match_threshold = fields.Float(
        string="Match threshold",
        digits=(16, 2),
        default=80.0,
        help="Fuzzy match scores below this (0–100) flag rows for manual review.",
    )
    line_ids = fields.One2many(
        "adventure.vendor.catalog.import.line",
        "batch_id",
        string="Lines",
    )
    mapping_ids = fields.One2many(
        "adventure.vendor.category.mapping",
        "batch_id",
        string="Category mappings",
    )
    line_count = fields.Integer(compute="_compute_line_stats", store=False)
    imported_count = fields.Integer(compute="_compute_line_stats", store=False)
    pending_count = fields.Integer(compute="_compute_line_stats", store=False)

    @api.depends("line_ids", "line_ids.state")
    def _compute_line_stats(self):
        for batch in self:
            lines = batch.line_ids
            batch.line_count = len(lines)
            batch.imported_count = len(lines.filtered(lambda l: l.state == "done"))
            batch.pending_count = len(lines.filtered(lambda l: l.state == "pending"))

    def action_recompute_categories(self):
        """Re-run fuzzy mapping for all pending lines and refresh mapping records."""
        Match = self.env["adventure.vendor_category_match"]
        Mapping = self.env["adventure.vendor.category.mapping"]
        for batch in self:
            if batch.state != "review":
                raise UserError(_("You can only remap batches in Review."))
            pending = batch.line_ids.filtered(lambda l: l.state == "pending")

            # Re-score every unique vendor category
            cache = {}
            for line in pending:
                key = (line.vendor_category or "").strip()
                if key not in cache:
                    cache[key] = Match.match_vendor_category(
                        key,
                        threshold=batch.match_threshold,
                    )

            # Update lines
            for line in pending:
                key = (line.vendor_category or "").strip()
                m = cache[key]
                line.write(
                    {
                        "categ_id": m["category_id"],
                        "match_confidence": m["confidence"],
                        "needs_review": m["needs_review"],
                    }
                )

            # Rebuild mapping records from scratch
            batch.mapping_ids.unlink()
            counts = {}
            for line in batch.line_ids:
                k = (line.vendor_category or "").strip()
                counts[k] = counts.get(k, 0) + 1
            mapping_vals = []
            for vkey, m in cache.items():
                mapping_vals.append(
                    {
                        "batch_id": batch.id,
                        "vendor_category": vkey,
                        "categ_id": m["category_id"],
                        "match_confidence": m["confidence"],
                        "needs_review": m["needs_review"],
                        "product_count": counts.get(vkey, 0),
                    }
                )
            Mapping.create(mapping_vals)
        return True

    def action_apply_mappings(self):
        """Push the category chosen in each mapping row down to every matching pending line."""
        self.ensure_one()
        if self.state != "review":
            raise UserError(_("You can only apply mappings to batches in Review."))
        for mapping in self.mapping_ids:
            lines = self.line_ids.filtered(
                lambda l, vc=mapping.vendor_category: (
                    (l.vendor_category or "").strip() == (vc or "").strip()
                    and l.state == "pending"
                )
            )
            lines.write(
                {
                    "categ_id": mapping.categ_id.id if mapping.categ_id else False,
                    "needs_review": not bool(mapping.categ_id),
                }
            )
        # Reload the form so the Product lines tab reflects the applied categories.
        # Returning True only works when self was modified; writing to related
        # line records requires an explicit act_window to trigger a UI refresh.
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_import_products(self):
        """Create ``product.template`` rows from pending lines (requires category)."""
        Template = self.env["product.template"]
        for batch in self:
            if batch.state != "review":
                raise UserError(_("Only batches in Review can be imported."))
            pending = batch.line_ids.filtered(lambda l: l.state == "pending")
            missing = pending.filtered(lambda l: not l.categ_id)
            if missing:
                raise UserError(
                    _(
                        "Assign a product category on every pending line before importing "
                        "(%s line(s) missing category)."
                    )
                    % len(missing)
                )
            for line in pending:
                tmpl = Template.create(
                    {
                        "name": line.product_name.strip(),
                        "categ_id": line.categ_id.id,
                        "type": "consu",
                        "sale_ok": True,
                        "purchase_ok": True,
                    }
                )
                line.write({"state": "done", "product_tmpl_id": tmpl.id})
            batch.state = "done"
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True


class AdventureVendorCatalogImportLine(models.Model):
    _name = "adventure.vendor.catalog.import.line"
    _description = "Vendor catalog import line"
    _order = "batch_id, sequence, id"

    batch_id = fields.Many2one(
        "adventure.vendor.catalog.import.batch",
        string="Batch",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    product_name = fields.Char(string="Product name", required=True)
    vendor_category = fields.Char(string="Vendor category")
    categ_id = fields.Many2one(
        "product.category",
        string="Product category",
        help="Mapped category; change before import if the suggestion is wrong.",
    )
    match_confidence = fields.Float(
        string="Match confidence",
        digits=(16, 2),
        readonly=True,
    )
    needs_review = fields.Boolean(
        string="Review suggested",
        readonly=True,
        help="True when the fuzzy score is below the batch threshold or no match was found.",
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("done", "Imported"),
        ],
        string="Line status",
        default="pending",
        required=True,
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Created product",
        readonly=True,
    )


class AdventureVendorCatalogImportWizard(models.TransientModel):
    _name = "adventure.vendor.catalog.import.wizard"
    _description = "Import vendor catalog from CSV"

    data_file = fields.Binary(string="CSV file", required=True)
    filename = fields.Char(string="Filename")
    match_threshold = fields.Float(
        string="Match threshold",
        digits=(16, 2),
        default=80.0,
    )
    delimiter = fields.Char(
        size=1,
        default=",",
        help="CSV field delimiter (comma by default).",
    )
    encoding = fields.Char(
        default="utf-8-sig",
        help="Text encoding (utf-8-sig handles Excel UTF-8 BOM).",
    )
    name_column = fields.Char(
        string="Product name column",
        default="Product Name",
        help="Header label for the product name column (matched case-insensitively).",
    )
    category_column = fields.Char(
        string="Vendor category column",
        default="Vendor Category",
        help="Header label for the vendor category column (matched case-insensitively).",
    )

    def _normalize_header_map(self, fieldnames):
        """Map lower-cased stripped header -> original header key from CSV."""
        return {((h or "").strip().lower()): h for h in fieldnames if h is not None}

    def _resolve_column(self, header_map, configured, fallbacks):
        key = (configured or "").strip().lower()
        if key in header_map:
            return header_map[key]
        for alt in fallbacks:
            k = alt.strip().lower()
            if k in header_map:
                return header_map[k]
        return None

    def _parse_csv_rows(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please upload a CSV file."))
        raw = base64.b64decode(self.data_file)
        dec = (self.encoding or "utf-8-sig").strip() or "utf-8-sig"
        try:
            text = raw.decode(dec)
        except UnicodeDecodeError as e:
            raise UserError(_("Could not decode CSV as %(enc)s: %(err)s") % {"enc": dec, "err": e}) from e

        delim = (self.delimiter or ",")[:1] or ","
        try:
            reader = csv.DictReader(io.StringIO(text), delimiter=delim)
        except csv.Error as e:
            raise UserError(_("Invalid CSV: %s") % e) from e

        if not reader.fieldnames:
            raise UserError(_("The CSV has no header row."))

        header_map = self._normalize_header_map(reader.fieldnames)
        name_key = self._resolve_column(
            header_map,
            self.name_column,
            ("product name", "product_name", "name", "title", "description"),
        )
        cat_key = self._resolve_column(
            header_map,
            self.category_column,
            (
                "vendor category",
                "vendor_category",
                "category",
                "product category",
                "vendor_cat",
            ),
        )
        if not name_key:
            raise UserError(
                _(
                    "Could not find a product name column. Headers: %(headers)s. "
                    "Expected something like '%(expected)s'."
                )
                % {
                    "headers": ", ".join(reader.fieldnames),
                    "expected": self.name_column,
                }
            )
        if not cat_key:
            raise UserError(
                _(
                    "Could not find a vendor category column. Headers: %(headers)s. "
                    "Expected something like '%(expected)s'."
                )
                % {
                    "headers": ", ".join(reader.fieldnames),
                    "expected": self.category_column,
                }
            )

        rows_out = []
        for i, row in enumerate(reader, start=2):
            pname = (row.get(name_key) or "").strip()
            vcat = (row.get(cat_key) or "").strip()
            if not pname:
                _logger.info("Skipping CSV row %s: empty product name", i)
                continue
            rows_out.append({"product_name": pname, "vendor_category": vcat})
        return rows_out

    def action_import(self):
        self.ensure_one()
        parsed = self._parse_csv_rows()
        if not parsed:
            raise UserError(_("No data rows with a product name were found in the file."))

        Batch = self.env["adventure.vendor.catalog.import.batch"]
        Line = self.env["adventure.vendor.catalog.import.line"]
        Mapping = self.env["adventure.vendor.category.mapping"]
        Match = self.env["adventure.vendor_category_match"]

        base_title = (self.filename or _("Vendor catalog")).strip()
        if base_title.lower().endswith(".csv"):
            base_title = base_title[:-4].strip() or _("Vendor catalog")
        batch = Batch.create(
            {
                "name": base_title,
                "source_filename": self.filename or _("upload.csv"),
                "match_threshold": self.match_threshold,
                "state": "review",
            }
        )

        # Count products per vendor category for the mapping summary
        vcat_counts = Counter(r["vendor_category"] for r in parsed)

        cache = {}
        seq = 10
        line_vals = []
        for rec in parsed:
            vkey = rec["vendor_category"]
            if vkey not in cache:
                cache[vkey] = Match.match_vendor_category(
                    vkey,
                    threshold=float(self.match_threshold),
                )
            m = cache[vkey]
            line_vals.append(
                {
                    "batch_id": batch.id,
                    "sequence": seq,
                    "product_name": rec["product_name"],
                    "vendor_category": rec["vendor_category"],
                    "categ_id": m["category_id"],
                    "match_confidence": m["confidence"],
                    "needs_review": m["needs_review"],
                }
            )
            seq += 10
        Line.create(line_vals)

        # One mapping row per unique vendor category for bulk review
        mapping_vals = [
            {
                "batch_id": batch.id,
                "vendor_category": vkey,
                "categ_id": cache[vkey]["category_id"],
                "match_confidence": cache[vkey]["confidence"],
                "needs_review": cache[vkey]["needs_review"],
                "product_count": vcat_counts[vkey],
            }
            for vkey in cache
        ]
        Mapping.create(mapping_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("Review import"),
            "res_model": "adventure.vendor.catalog.import.batch",
            "res_id": batch.id,
            "view_mode": "form",
            "target": "current",
        }
