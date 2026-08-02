# -*- coding: utf-8 -*-

import base64
import logging
import os
import re
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.smartwaiver_client import (
    SmartwaiverAPIError,
    SmartwaiverClient,
)

_logger = logging.getLogger(__name__)

PARAM_API_KEY = "adventure_smartwaiver.api_key"
PARAM_ENABLED = "adventure_smartwaiver.sync_enabled"
PARAM_BASE_URL = "adventure_smartwaiver.base_url"
PARAM_TEMPLATE_IDS = "adventure_smartwaiver.template_ids"
PARAM_LAST_POLL_AT = "adventure_smartwaiver.last_poll_at"
PARAM_FETCH_PDF_DEFAULT = "adventure_smartwaiver.fetch_pdf_default"


def _normalize_email(value):
    if not value:
        return ""
    return value.strip().lower()


def _normalize_name_part(value):
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", value.strip().lower())
    return cleaned


def _parse_smartwaiver_dt(value):
    if not value:
        return False
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+0000"
    text = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", text)
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
        except ValueError:
            continue
    # Truncate fractional seconds if present.
    if "." in text:
        head, _sep, rest = text.partition(".")
        tz = ""
        for sign in ("+", "-"):
            if sign in rest:
                idx = rest.index(sign)
                tz = rest[idx:]
                break
        return _parse_smartwaiver_dt(head + tz)
    return False


class SmartwaiverWaiver(models.Model):
    _name = "smartwaiver.waiver"
    _description = "Smartwaiver signed waiver"
    _order = "created_on desc, id desc"
    _rec_name = "display_name"

    waiver_id = fields.Char(
        string="Smartwaiver ID",
        required=True,
        index=True,
        copy=False,
    )
    template_id = fields.Char(string="Template ID", index=True)
    title = fields.Char()
    created_on = fields.Datetime(index=True)
    expiration_date = fields.Date()
    expired = fields.Boolean(default=False, index=True)
    verified = fields.Boolean(default=False)
    kiosk = fields.Boolean(default=False)

    email = fields.Char(index=True)
    first_name = fields.Char()
    middle_name = fields.Char()
    last_name = fields.Char()
    email_normalized = fields.Char(index=True)
    name_normalized = fields.Char(index=True)

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        index=True,
        ondelete="set null",
    )
    match_state = fields.Selection(
        [
            ("matched", "Matched"),
            ("unmatched", "Unmatched"),
            ("manual", "Manual"),
            ("ambiguous", "Ambiguous"),
        ],
        default="unmatched",
        required=True,
        index=True,
    )
    match_method = fields.Selection(
        [
            ("email", "Email"),
            ("name", "Name"),
            ("manual", "Manual"),
            ("none", "None"),
        ],
        default="none",
        required=True,
    )
    match_notes = fields.Text()

    participant_payload = fields.Json(string="Participants")
    custom_fields = fields.Json(string="Custom fields")
    raw_payload = fields.Json(string="Raw payload fragment")
    last_sync_at = fields.Datetime()

    pdf_attachment_id = fields.Many2one(
        "ir.attachment",
        string="PDF",
        ondelete="set null",
        copy=False,
    )
    display_name = fields.Char(compute="_compute_display_name", store=True)

    _sql_constraints = [
        (
            "smartwaiver_waiver_id_uniq",
            "unique(waiver_id)",
            "Smartwaiver waiver ID must be unique.",
        ),
    ]

    @api.depends("title", "first_name", "last_name", "waiver_id")
    def _compute_display_name(self):
        for rec in self:
            person = " ".join(p for p in [rec.first_name, rec.last_name] if p).strip()
            if rec.title and person:
                rec.display_name = f"{rec.title} — {person}"
            elif person:
                rec.display_name = person
            elif rec.title:
                rec.display_name = rec.title
            else:
                rec.display_name = rec.waiver_id or _("Waiver")

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    @api.model
    def _get_api_key(self):
        env_key = (os.environ.get("SMARTWAIVER_API_KEY") or "").strip()
        if env_key:
            return env_key
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_API_KEY, default="")
            .strip()
        )

    @api.model
    def _sync_enabled(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_ENABLED, default="False")
            == "True"
        )

    @api.model
    def _template_allowlist(self):
        raw = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_TEMPLATE_IDS, default="")
            or ""
        )
        return {part.strip() for part in raw.split(",") if part.strip()}

    @api.model
    def _get_client(self):
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_BASE_URL, default="")
            .strip()
            or None
        )
        return SmartwaiverClient(api_key=self._get_api_key(), base_url=base_url)

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    @api.model
    def _partners_for_email(self, email):
        normalized = _normalize_email(email)
        if not normalized:
            return self.env["res.partner"]
        partners = self.env["res.partner"].search([("email", "ilike", normalized)])
        return partners.filtered(lambda p: _normalize_email(p.email) == normalized)

    @api.model
    def _partners_for_name(self, first_name, last_name):
        first = _normalize_name_part(first_name)
        last = _normalize_name_part(last_name)
        if not first or not last:
            return self.env["res.partner"]
        # Prefer exact first+last equality after normalize; search broadly then filter.
        domain = [
            ("name", "ilike", first),
            ("name", "ilike", last),
        ]
        candidates = self.env["res.partner"].search(domain, limit=50)
        exact = self.env["res.partner"]
        for partner in candidates:
            parts = _normalize_name_part(partner.name).split(" ")
            if len(parts) >= 2 and parts[0] == first and parts[-1] == last:
                exact |= partner
            elif (
                _normalize_name_part(getattr(partner, "firstname", "") or "") == first
                and _normalize_name_part(getattr(partner, "lastname", "") or "") == last
            ):
                exact |= partner
        return exact

    def _apply_auto_match(self):
        """Resolve partner for records that are not manually linked."""
        for waiver in self:
            if waiver.match_state == "manual" and waiver.partner_id:
                continue
            partners = self._partners_for_email(waiver.email)
            if partners:
                if len(partners) == 1:
                    waiver.write(
                        {
                            "partner_id": partners.id,
                            "match_state": "matched",
                            "match_method": "email",
                            "match_notes": False,
                        }
                    )
                else:
                    waiver.write(
                        {
                            "partner_id": False,
                            "match_state": "ambiguous",
                            "match_method": "none",
                            "match_notes": _(
                                "Multiple partners share email %s"
                            )
                            % (waiver.email_normalized or waiver.email),
                        }
                    )
                continue

            partners = self._partners_for_name(waiver.first_name, waiver.last_name)
            if partners:
                if len(partners) == 1:
                    waiver.write(
                        {
                            "partner_id": partners.id,
                            "match_state": "matched",
                            "match_method": "name",
                            "match_notes": False,
                        }
                    )
                else:
                    waiver.write(
                        {
                            "partner_id": False,
                            "match_state": "ambiguous",
                            "match_method": "none",
                            "match_notes": _(
                                "Multiple partners match name %s %s"
                            )
                            % (waiver.first_name or "", waiver.last_name or ""),
                        }
                    )
                continue

            waiver.write(
                {
                    "partner_id": False,
                    "match_state": "unmatched",
                    "match_method": "none",
                    "match_notes": False,
                }
            )

    @api.model
    def rematch_unmatched_for_email(self, email):
        normalized = _normalize_email(email)
        if not normalized:
            return self.browse()
        waivers = self.search(
            [
                ("email_normalized", "=", normalized),
                ("match_state", "in", ("unmatched", "ambiguous")),
            ]
        )
        waivers._apply_auto_match()
        return waivers

    def action_open_link_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Link waiver to customer"),
            "res_model": "smartwaiver.link.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_waiver_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_unlink_partner(self):
        for waiver in self:
            waiver.write(
                {
                    "partner_id": False,
                    "match_state": "unmatched",
                    "match_method": "none",
                    "match_notes": _("Manually unlinked"),
                }
            )
        return True

    def action_rematch(self):
        auto = self.filtered(lambda w: w.match_state != "manual")
        auto._apply_auto_match()
        return True

    # ------------------------------------------------------------------
    # Upsert from API payloads
    # ------------------------------------------------------------------

    @api.model
    def _vals_from_payload(self, payload):
        email = payload.get("email") or ""
        first = payload.get("firstName") or ""
        last = payload.get("lastName") or ""
        expiration_raw = payload.get("expirationDate") or ""
        expiration_date = False
        if expiration_raw:
            parsed = _parse_smartwaiver_dt(expiration_raw)
            expiration_date = parsed.date() if parsed else False

        custom = payload.get("customWaiverFields") or payload.get("custom_fields") or {}
        participants = payload.get("participants") or []
        return {
            "waiver_id": payload.get("waiverId") or payload.get("waiver_id"),
            "template_id": payload.get("templateId") or payload.get("template_id") or False,
            "title": payload.get("title") or False,
            "created_on": _parse_smartwaiver_dt(payload.get("createdOn") or payload.get("created_on")),
            "expiration_date": expiration_date,
            "expired": bool(payload.get("expired")),
            "verified": bool(payload.get("verified")),
            "kiosk": bool(payload.get("kiosk")),
            "email": email or False,
            "first_name": first or False,
            "middle_name": payload.get("middleName") or False,
            "last_name": last or False,
            "email_normalized": _normalize_email(email) or False,
            "name_normalized": (
                f"{_normalize_name_part(first)} {_normalize_name_part(last)}".strip()
                or False
            ),
            "participant_payload": participants,
            "custom_fields": custom,
            "raw_payload": {
                "waiverId": payload.get("waiverId"),
                "templateId": payload.get("templateId"),
                "email": email,
                "firstName": first,
                "lastName": last,
                "tags": payload.get("tags") or [],
            },
            "last_sync_at": fields.Datetime.now(),
        }

    @api.model
    def upsert_from_payload(self, payload, auto_match=True):
        vals = self._vals_from_payload(payload)
        waiver_id = vals.get("waiver_id")
        if not waiver_id:
            raise UserError(_("Smartwaiver payload is missing waiverId."))

        allowlist = self._template_allowlist()
        template_id = vals.get("template_id") or ""
        if allowlist and template_id and template_id not in allowlist:
            _logger.info(
                "Skipping Smartwaiver waiver %s (template %s not in allowlist)",
                waiver_id,
                template_id,
            )
            return self.browse()

        existing = self.search([("waiver_id", "=", waiver_id)], limit=1)
        if existing:
            # Preserve manual links.
            write_vals = dict(vals)
            if existing.match_state == "manual":
                write_vals.pop("partner_id", None)
            existing.write(write_vals)
            record = existing
        else:
            record = self.create(vals)

        if auto_match and record.match_state != "manual":
            record._apply_auto_match()
        return record

    def action_fetch_pdf(self):
        client = self._get_client()
        Attachment = self.env["ir.attachment"].sudo()
        for waiver in self:
            try:
                detail = client.get_waiver(waiver.waiver_id, pdf=True)
            except SmartwaiverAPIError as exc:
                raise UserError(_("Smartwaiver PDF fetch failed: %s") % exc) from exc
            pdf_b64 = detail.get("pdf")
            if not pdf_b64:
                raise UserError(
                    _("Smartwaiver did not return a PDF for waiver %s.") % waiver.waiver_id
                )
            # API may return raw base64; normalize padding.
            pdf_bytes = base64.b64decode(pdf_b64)
            pdf_stored = base64.b64encode(pdf_bytes)
            name = f"smartwaiver-{waiver.waiver_id}.pdf"
            if waiver.pdf_attachment_id:
                waiver.pdf_attachment_id.write(
                    {
                        "name": name,
                        "datas": pdf_stored,
                        "mimetype": "application/pdf",
                    }
                )
                attachment = waiver.pdf_attachment_id
            else:
                attachment = Attachment.create(
                    {
                        "name": name,
                        "type": "binary",
                        "datas": pdf_stored,
                        "res_model": self._name,
                        "res_id": waiver.id,
                        "mimetype": "application/pdf",
                    }
                )
                waiver.pdf_attachment_id = attachment.id
            # Refresh metadata from detail without requiring rematch.
            self.upsert_from_payload(detail, auto_match=False)
        return True

    # ------------------------------------------------------------------
    # Sync jobs
    # ------------------------------------------------------------------

    @api.model
    def cron_poll_waivers(self, limit=50):
        if not self._sync_enabled():
            _logger.debug("Smartwaiver sync disabled; skipping poll.")
            return False
        try:
            client = self._get_client()
        except SmartwaiverAPIError as exc:
            _logger.warning("Smartwaiver poll skipped: %s", exc)
            return False

        ICP = self.env["ir.config_parameter"].sudo()
        from_dts = ICP.get_param(PARAM_LAST_POLL_AT, default="") or ""
        allowlist = self._template_allowlist()
        template_id = ""
        if len(allowlist) == 1:
            template_id = next(iter(allowlist))

        try:
            summaries = client.get_waiver_summaries(
                limit=limit,
                template_id=template_id or None,
                from_dts=from_dts or None,
            )
        except SmartwaiverAPIError as exc:
            _logger.warning("Smartwaiver poll failed: %s", exc)
            return False

        newest = from_dts
        for summary in summaries:
            waiver_id = summary.get("waiverId")
            if not waiver_id:
                continue
            try:
                detail = client.get_waiver(waiver_id, pdf=False)
            except SmartwaiverAPIError as exc:
                _logger.warning("Smartwaiver get_waiver %s failed: %s", waiver_id, exc)
                self.upsert_from_payload(summary)
                continue
            self.upsert_from_payload(detail or summary)
            created = detail.get("createdOn") or summary.get("createdOn") or ""
            if created and (not newest or created > newest):
                newest = created

        if newest:
            ICP.set_param(PARAM_LAST_POLL_AT, newest)
        return True

    @api.model
    def action_sync_now(self):
        if not self._get_api_key():
            raise UserError(
                _(
                    "Configure a Smartwaiver API key in Settings or "
                    "SMARTWAIVER_API_KEY before syncing."
                )
            )
        # Allow manual sync even if the cron flag is off.
        self.env["ir.config_parameter"].sudo().set_param(PARAM_ENABLED, "True")
        self.cron_poll_waivers()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Smartwaiver"),
                "message": _("Waiver sync completed."),
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def cron_drain_webhook_queue(self, max_messages=25):
        if not self._sync_enabled():
            return False
        try:
            client = self._get_client()
        except SmartwaiverAPIError as exc:
            _logger.warning("Smartwaiver webhook drain skipped: %s", exc)
            return False

        processed = 0
        for _ in range(max_messages):
            try:
                message = client.get_webhook_queue_account_message(delete=False)
            except SmartwaiverAPIError as exc:
                # Empty queue often returns 404 / data_error — stop quietly.
                if exc.status_code in (404, 402):
                    break
                _logger.warning("Smartwaiver webhook drain error: %s", exc)
                break

            if not message or not isinstance(message, dict):
                break

            payload = message.get("payload") or {}
            if not isinstance(payload, dict):
                payload = {}
            waiver_id = (
                payload.get("uniqueId")
                or payload.get("unique_id")
                or message.get("unique_id")
                or message.get("waiverId")
                or message.get("waiver_id")
            )
            message_id = message.get("messageId") or message.get("message_id")
            if waiver_id:
                try:
                    detail = client.get_waiver(waiver_id, pdf=False)
                    self.upsert_from_payload(detail)
                except SmartwaiverAPIError as exc:
                    _logger.warning(
                        "Smartwaiver webhook waiver %s fetch failed: %s",
                        waiver_id,
                        exc,
                    )
                    # Leave the queue message for a later retry.
                    break
            if message_id:
                try:
                    client.delete_webhook_queue_account_message(message_id)
                except SmartwaiverAPIError as exc:
                    _logger.warning(
                        "Smartwaiver webhook message delete %s failed: %s",
                        message_id,
                        exc,
                    )
                    break
            processed += 1
        return processed

    @api.model
    def search_and_import_for_partner(self, partner):
        partner.ensure_one()
        client = self._get_client()
        imported = self.browse()
        guids = []
        email = _normalize_email(partner.email)
        if email:
            try:
                guids.append(client.search(email=email))
            except SmartwaiverAPIError as exc:
                raise UserError(_("Smartwaiver search failed: %s") % exc) from exc
        # Name search as fallback / supplement.
        name_parts = (partner.name or "").strip().split()
        if len(name_parts) >= 2:
            try:
                guids.append(
                    client.search(first_name=name_parts[0], last_name=name_parts[-1])
                )
            except SmartwaiverAPIError as exc:
                _logger.warning("Smartwaiver name search failed: %s", exc)

        seen = set()
        for guid in guids:
            if not guid:
                continue
            page = 0
            while page < 5:
                try:
                    results = client.search_results(guid, page=page, pdf=False)
                except SmartwaiverAPIError:
                    break
                if not results:
                    break
                for payload in results:
                    wid = payload.get("waiverId")
                    if not wid or wid in seen:
                        continue
                    seen.add(wid)
                    imported |= self.upsert_from_payload(payload)
                page += 1
        return imported
