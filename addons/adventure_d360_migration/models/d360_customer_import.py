# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AdventureD360CustomerImportBatch(models.Model):
    _name = "adventure.d360.customer.import.batch"
    _description = "D360 customer import batch"
    _order = "id desc"

    _PROGRESS_FIELD_NAMES = [
        "line_count",
        "pending_count",
        "review_needed_count",
        "processed_count",
        "imported_count",
        "failed_count",
        "person_count",
        "company_count",
        "ambiguous_count",
        "progress_percent",
        "state",
        "last_upsert_at",
    ]

    name = fields.Char(required=True)
    state = fields.Selection(
        [
            ("review", "Review"),
            ("done", "Imported"),
            ("cancelled", "Cancelled"),
        ],
        default="review",
        required=True,
    )
    shop_name = fields.Char(string="Shop")
    source_filename = fields.Char(string="Source file")
    source_checksum = fields.Char(string="SHA256")
    source_encoding = fields.Char(string="Encoding")
    source_delimiter = fields.Char(string="Delimiter")
    upload_notes = fields.Text(string="Source notes")
    last_upsert_at = fields.Datetime(string="Last upsert at", readonly=True)
    line_ids = fields.One2many(
        "adventure.d360.customer.import.line",
        "batch_id",
        string="Source rows",
    )
    pending_line_ids = fields.One2many(
        "adventure.d360.customer.import.line",
        "batch_id",
        string="Pending source rows",
        domain=[("import_state", "=", "pending")],
    )
    show_pending_only = fields.Boolean(
        string="Pending only",
        default=False,
        help="Show only rows whose import state is still Pending in the review table.",
    )
    line_count = fields.Integer(compute="_compute_counts")
    pending_count = fields.Integer(compute="_compute_counts")
    review_needed_count = fields.Integer(compute="_compute_counts")
    processed_count = fields.Integer(compute="_compute_counts")
    imported_count = fields.Integer(compute="_compute_counts")
    failed_count = fields.Integer(compute="_compute_counts")
    person_count = fields.Integer(compute="_compute_counts")
    company_count = fields.Integer(compute="_compute_counts")
    ambiguous_count = fields.Integer(compute="_compute_counts")
    progress_percent = fields.Float(compute="_compute_counts")

    @api.depends(
        "line_ids",
        "line_ids.import_state",
        "line_ids.review_needed",
        "line_ids.partner_kind_guess",
    )
    def _compute_counts(self):
        if not self:
            return
        stats = {
            batch.id: {
                "line_count": 0,
                "pending_count": 0,
                "review_needed_count": 0,
                "processed_count": 0,
                "imported_count": 0,
                "failed_count": 0,
                "person_count": 0,
                "company_count": 0,
                "ambiguous_count": 0,
                "progress_percent": 0.0,
            }
            for batch in self
        }
        Line = self.env["adventure.d360.customer.import.line"]
        grouped_counts = Line.read_group(
            [("batch_id", "in", self.ids)],
            ["batch_id", "import_state", "partner_kind_guess"],
            ["batch_id", "import_state", "partner_kind_guess"],
            lazy=False,
        )
        for group in grouped_counts:
            batch_id = group["batch_id"][0]
            count = group["__count"]
            batch_stats = stats[batch_id]
            batch_stats["line_count"] += count

            import_state = group.get("import_state")
            if import_state == "imported":
                batch_stats["imported_count"] += count
            elif import_state == "failed":
                batch_stats["failed_count"] += count
            elif import_state == "pending":
                batch_stats["pending_count"] += count

            partner_kind = group.get("partner_kind_guess")
            if partner_kind == "person":
                batch_stats["person_count"] += count
            elif partner_kind == "company":
                batch_stats["company_count"] += count
            elif partner_kind == "ambiguous":
                batch_stats["ambiguous_count"] += count

        review_groups = Line.read_group(
            [("batch_id", "in", self.ids), ("review_needed", "=", True)],
            ["batch_id"],
            ["batch_id"],
            lazy=False,
        )
        for group in review_groups:
            batch_id = group["batch_id"][0]
            stats[batch_id]["review_needed_count"] = group["__count"]

        for batch in self:
            batch_stats = stats[batch.id]
            batch_stats["processed_count"] = (
                batch_stats["imported_count"] + batch_stats["failed_count"]
            )
            if batch_stats["line_count"]:
                batch_stats["progress_percent"] = (
                    batch_stats["processed_count"] * 100.0 / batch_stats["line_count"]
                )
            for field_name, value in batch_stats.items():
                setattr(batch, field_name, value)

    def _get_progress_values(self):
        self.ensure_one()
        return self.read(self._PROGRESS_FIELD_NAMES)[0]

    def _format_line_import_error(self, error):
        message = (getattr(error, "name", False) or str(error) or "").strip()
        return message or _("Unknown error while upserting this row.")

    def _get_pending_upsert_line_domain(self):
        self.ensure_one()
        return [
            ("batch_id", "=", self.id),
            ("import_state", "=", "pending"),
            ("partner_kind_guess", "!=", "ambiguous"),
        ]

    def _has_pending_upsert_lines(self):
        self.ensure_one()
        return bool(
            self.env["adventure.d360.customer.import.line"].search_count(
                self._get_pending_upsert_line_domain()
            )
        )

    def _upsert_line_partner(self, line):
        self.ensure_one()
        line.ensure_one()
        if not line.source_customer_id:
            raise UserError(
                _(
                    "Row %(row)s has no Customer ID, so it cannot be used for an upsert."
                )
                % {"row": line.sequence}
            )
        Partner = self.env["res.partner"]
        partner = Partner.search(
            [("d360_customer_id", "=", line.source_customer_id)],
            limit=1,
        )
        vals = line.prepare_partner_vals()
        if partner:
            partner.write(vals)
        else:
            partner = Partner.create(vals)
        line.write(
            {
                "partner_id": partner.id,
                "import_state": "imported",
                "import_error": False,
            }
        )

    def _finalize_upsert_if_complete(self):
        self.ensure_one()
        pending_count = self.env["adventure.d360.customer.import.line"].search_count(
            [("batch_id", "=", self.id), ("import_state", "=", "pending")]
        )
        if pending_count:
            return False
        self.write(
            {
                "state": "done",
                "last_upsert_at": fields.Datetime.now(),
            }
        )
        return True

    def action_upsert_partners_chunk(self, chunk_size=250):
        self.ensure_one()
        if self.state == "cancelled":
            raise UserError(_("Cancelled batches cannot be upserted."))

        chunk_size = max(1, min(int(chunk_size or 250), 1000))
        Line = self.env["adventure.d360.customer.import.line"]
        lines = Line.search(
            self._get_pending_upsert_line_domain(),
            limit=chunk_size,
            order="sequence, id",
        )
        if not lines:
            batch_done = False
            if not self.env["adventure.d360.customer.import.line"].search_count(
                [("batch_id", "=", self.id), ("import_state", "=", "pending")]
            ):
                batch_done = self._finalize_upsert_if_complete()
            return {
                "success": True,
                "done": True,
                "batch_done": batch_done,
                "batch_values": self._get_progress_values(),
            }

        for line in lines:
            try:
                with self.env.cr.savepoint():
                    self._upsert_line_partner(line)
            except Exception as error:
                line.write(
                    {
                        "import_state": "failed",
                        "import_error": self._format_line_import_error(error),
                    }
                )

        done = not self._has_pending_upsert_lines()
        batch_done = False
        if done and not self.env["adventure.d360.customer.import.line"].search_count(
            [("batch_id", "=", self.id), ("import_state", "=", "pending")]
        ):
            batch_done = self._finalize_upsert_if_complete()
        return {
            "success": True,
            "done": done,
            "batch_done": batch_done,
            "batch_values": self._get_progress_values(),
        }

    def action_recompute_classification(self):
        for batch in self:
            if batch.state != "review":
                raise UserError(_("You can only reclassify batches in Review."))
            for line in batch.line_ids:
                line.action_recompute_classification()
        return True

    def action_upsert_partners(self):
        for batch in self:
            if batch.state != "review":
                raise UserError(_("Only batches in Review can be upserted."))
            while True:
                result = batch.action_upsert_partners_chunk()
                if result.get("done"):
                    break
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True


class AdventureD360CustomerImportLine(models.Model):
    _name = "adventure.d360.customer.import.line"
    _description = "D360 customer import line"
    _order = "batch_id, sequence, id"

    _PARTNER_KIND_SELECTION = [
        ("person", "Person"),
        ("company", "Company"),
        ("ambiguous", "Ambiguous"),
    ]
    _CONFIDENCE_SELECTION = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]
    _PLACEHOLDERS = {"", " ", ".", "undefined", "0000-00-00"}
    _CONSUMER_EMAIL_DOMAINS = {
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "live.com",
        "aol.com",
        "icloud.com",
        "me.com",
        "comcast.net",
        "verizon.net",
        "msn.com",
    }
    _ROLE_MAILBOXES = {
        "sales",
        "info",
        "orders",
        "operations",
        "support",
        "service",
        "admin",
        "northamerica",
    }
    _COMPANY_KEYWORDS = {
        "inc",
        "corp",
        "corporation",
        "llc",
        "ltd",
        "company",
        "co",
        "shop",
        "scuba",
        "dive",
        "aquatics",
        "express",
        "agency",
        "association",
        "university",
        "rite",
        "gear",
        "masonry",
        "sports",
        "bag",
        "force",
    }
    _KNOWN_BRANDS = {
        "fourth element",
        "innovative scuba concepts",
        "padi",
        "ssi",
        "dive rite",
        "scubapro",
        "dive gear express",
        "scuba force usa",
        "carter bag inc",
        "lavacore",
        "hog",
        "dui",
        "xsscuba",
        "princeton tec dive",
    }

    batch_id = fields.Many2one(
        "adventure.d360.customer.import.batch",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    source_customer_id = fields.Char(string="Customer ID", required=True)
    mailing_name = fields.Char()
    address_line_0 = fields.Char(string="Address line 0")
    address_line_1 = fields.Char(string="Address line 1")
    city = fields.Char()
    state_name = fields.Char(string="State / region")
    zip_code = fields.Char(string="ZIP")
    country_name = fields.Char(string="Country")
    last_name = fields.Char()
    first_name = fields.Char()
    middle_initial = fields.Char()
    gender = fields.Char()
    email = fields.Char()
    home_phone = fields.Char()
    work_phone = fields.Char()
    mobile_phone = fields.Char()
    primary_mailing_list = fields.Boolean(string="Primary mailing list")
    birthday = fields.Date()
    customer_type = fields.Char()
    invoice_type = fields.Char()
    last_purchase_date = fields.Date()
    partner_display_name = fields.Char(
        string="Partner name",
        compute="_compute_partner_display_name",
        store=False,
    )
    partner_kind_guess = fields.Selection(
        selection=_PARTNER_KIND_SELECTION,
        string="Partner kind",
        default="ambiguous",
        required=True,
    )
    classification_confidence = fields.Selection(
        selection=_CONFIDENCE_SELECTION,
        string="Confidence",
        default="low",
        required=True,
    )
    classification_reasons = fields.Text(readonly=True)
    review_needed = fields.Boolean(default=False)
    import_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("imported", "Imported"),
            ("failed", "Failed"),
        ],
        default="pending",
        required=True,
    )
    partner_id = fields.Many2one("res.partner", readonly=True)
    import_error = fields.Text(readonly=True)

    @api.depends("first_name", "last_name", "mailing_name", "partner_kind_guess")
    def _compute_partner_display_name(self):
        for line in self:
            line.partner_display_name = line._derive_display_name()

    @api.model
    def _clean_value(self, value):
        cleaned = (value or "").strip()
        return "" if cleaned.lower() in self._PLACEHOLDERS else cleaned

    @api.model
    def _looks_like_company_name(self, value):
        cleaned = self._clean_value(value).lower()
        if not cleaned:
            return False
        tokens = {token.strip(".,") for token in cleaned.replace("/", " ").split()}
        if cleaned in self._KNOWN_BRANDS:
            return True
        return bool(tokens & self._COMPANY_KEYWORDS)

    @api.model
    def classify_source_values(self, values):
        first_name = self._clean_value(values.get("first_name"))
        last_name = self._clean_value(values.get("last_name"))
        mailing_name = self._clean_value(values.get("mailing_name"))
        middle_initial = self._clean_value(values.get("middle_initial"))
        gender = self._clean_value(values.get("gender")).lower()
        email = self._clean_value(values.get("email")).lower()
        customer_type = self._clean_value(values.get("customer_type")).lower()
        invoice_type = self._clean_value(values.get("invoice_type")).lower()
        address_line_1 = self._clean_value(values.get("address_line_1"))

        person_score = 0
        company_score = 0
        reasons = []

        if first_name and first_name not in {"-", "."}:
            person_score += 2
            reasons.append(_("First name present"))
        if last_name:
            person_score += 1
            reasons.append(_("Last name present"))
        if middle_initial:
            person_score += 1
            reasons.append(_("Middle initial present"))
        if gender in {"male", "female"}:
            person_score += 2
            reasons.append(_("Gender looks person-specific"))
        if values.get("birthday"):
            person_score += 2
            reasons.append(_("Birthday present"))
        if customer_type == "retail":
            person_score += 1
            reasons.append(_("Customer type is Retail"))
        if invoice_type == "retail":
            person_score += 1
            reasons.append(_("Invoice type is Retail"))

        if email and "@" in email:
            local_part, domain = email.split("@", 1)
            if domain in self._CONSUMER_EMAIL_DOMAINS:
                person_score += 1
                reasons.append(_("Consumer email domain"))
            if local_part in self._ROLE_MAILBOXES:
                company_score += 2
                reasons.append(_("Role mailbox email"))

        if not first_name and (last_name or mailing_name):
            company_score += 2
            reasons.append(_("No first name on row"))
        if self._looks_like_company_name(last_name) or self._looks_like_company_name(mailing_name):
            company_score += 3
            reasons.append(_("Name includes organization-style keywords"))
        if address_line_1 and "suite" in address_line_1.lower():
            company_score += 1
            reasons.append(_("Suite-style address"))

        if company_score >= person_score + 2 and company_score >= 3:
            partner_kind = "company"
        elif person_score >= company_score + 2 and person_score >= 3:
            partner_kind = "person"
        else:
            partner_kind = "ambiguous"
            reasons.append(_("Mixed or weak signals"))

        high_score = max(person_score, company_score)
        diff = abs(person_score - company_score)
        if partner_kind != "ambiguous" and high_score >= 4 and diff >= 3:
            confidence = "high"
        elif partner_kind != "ambiguous" and high_score >= 3 and diff >= 2:
            confidence = "medium"
        else:
            confidence = "low"

        review_needed = partner_kind == "ambiguous" or confidence == "low"
        return {
            "partner_kind_guess": partner_kind,
            "classification_confidence": confidence,
            "classification_reasons": "; ".join(reasons),
            "review_needed": review_needed,
        }

    def _derive_display_name(self):
        self.ensure_one()
        if self.partner_kind_guess == "company":
            return (
                self._clean_value(self.last_name)
                or self._clean_value(self.mailing_name)
                or self.source_customer_id
            )
        full_name = " ".join(
            part for part in [self._clean_value(self.first_name), self._clean_value(self.last_name)] if part
        ).strip()
        return full_name or self._clean_value(self.mailing_name) or self.source_customer_id

    def _set_manual_partner_kind(self, partner_kind):
        confidence = "low" if partner_kind == "ambiguous" else "high"
        reasons = {
            "person": _("Manually marked as Person"),
            "company": _("Manually marked as Company"),
            "ambiguous": _("Manually reset to Ambiguous"),
        }
        self.write(
            {
                "partner_kind_guess": partner_kind,
                "classification_confidence": confidence,
                "classification_reasons": reasons[partner_kind],
                "review_needed": partner_kind == "ambiguous",
            }
        )
        return True

    def _match_country(self):
        self.ensure_one()
        country_name = self._clean_value(self.country_name)
        if not country_name:
            return self.env["res.country"]
        Country = self.env["res.country"]
        country = Country.search([("name", "=ilike", country_name)], limit=1)
        if not country and len(country_name) == 2:
            country = Country.search([("code", "=", country_name.upper())], limit=1)
        return country

    def _match_state(self, country):
        self.ensure_one()
        state_name = self._clean_value(self.state_name)
        if not state_name:
            return self.env["res.country.state"]
        State = self.env["res.country.state"]
        domain = [("name", "=ilike", state_name)]
        if country:
            domain.append(("country_id", "=", country.id))
        state = State.search(domain, limit=1)
        if not state and len(state_name) <= 3:
            code_domain = [("code", "=", state_name.upper())]
            if country:
                code_domain.append(("country_id", "=", country.id))
            state = State.search(code_domain, limit=1)
        return state

    def prepare_partner_vals(self):
        self.ensure_one()
        country = self._match_country()
        state = self._match_state(country)
        phone = self._clean_value(self.home_phone) or self._clean_value(self.work_phone)
        vals = {
            "name": self._derive_display_name(),
            "company_type": "company" if self.partner_kind_guess == "company" else "person",
            "is_company": self.partner_kind_guess == "company",
            "email": self._clean_value(self.email) or False,
            "phone": phone or False,
            "mobile": self._clean_value(self.mobile_phone) or False,
            "street": self._clean_value(self.address_line_0) or False,
            "street2": self._clean_value(self.address_line_1) or False,
            "city": self._clean_value(self.city) or False,
            "zip": self._clean_value(self.zip_code) or False,
            "d360_customer_id": self.source_customer_id,
            "d360_external_ref": "d360.partner.%s" % self.source_customer_id,
            "d360_partner_kind": self.partner_kind_guess,
            "d360_customer_type": self._clean_value(self.customer_type) or False,
            "d360_invoice_type": self._clean_value(self.invoice_type) or False,
            "d360_last_purchase_date": self.last_purchase_date or False,
            "d360_birthday": self.birthday or False,
            "d360_last_import_batch_id": self.batch_id.id,
        }
        if country:
            vals["country_id"] = country.id
        if state:
            vals["state_id"] = state.id
        return vals

    def action_set_person(self):
        return self.action_set_partner_kind("person")

    def action_set_company(self):
        return self.action_set_partner_kind("company")

    def action_set_ambiguous(self):
        return self.action_set_partner_kind("ambiguous")

    def action_set_partner_kind(self, partner_kind):
        if partner_kind not in {"person", "company", "ambiguous"}:
            raise UserError(_("Unsupported partner kind '%s'.") % partner_kind)
        for line in self:
            line._set_manual_partner_kind(partner_kind)
        result = {"success": True}
        batches = self.mapped("batch_id")
        if len(batches) == 1:
            result["batch_values"] = batches.read(
                [
                    "line_count",
                    "pending_count",
                    "review_needed_count",
                    "imported_count",
                    "person_count",
                    "company_count",
                    "ambiguous_count",
                ]
            )[0]
        return result

    def action_recompute_classification(self):
        for line in self:
            values = {
                "mailing_name": line.mailing_name,
                "last_name": line.last_name,
                "first_name": line.first_name,
                "middle_initial": line.middle_initial,
                "gender": line.gender,
                "email": line.email,
                "birthday": line.birthday,
                "customer_type": line.customer_type,
                "invoice_type": line.invoice_type,
                "address_line_1": line.address_line_1,
            }
            line.write(line.classify_source_values(values))
        return True
