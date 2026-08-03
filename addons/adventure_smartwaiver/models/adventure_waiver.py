# -*- coding: utf-8 -*-
"""Smartwaiver provider connector for adventure.waiver."""

import base64
import logging
import os
import re
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.smartwaiver_client import SmartwaiverAPIError, SmartwaiverClient
from odoo.addons.adventure_waiver.models.adventure_waiver import normalize_email

_logger = logging.getLogger(__name__)

PROVIDER = "smartwaiver"
PARAM_API_KEY = "adventure_smartwaiver.api_key"
PARAM_ENABLED = "adventure_smartwaiver.sync_enabled"
PARAM_BASE_URL = "adventure_smartwaiver.base_url"
PARAM_TEMPLATE_IDS = "adventure_smartwaiver.template_ids"
PARAM_LAST_POLL_AT = "adventure_smartwaiver.last_poll_at"
PARAM_FETCH_PDF_DEFAULT = "adventure_smartwaiver.fetch_pdf_default"


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


class AdventureWaiver(models.Model):
    _inherit = "adventure.waiver"

    provider = fields.Selection(
        selection_add=[(PROVIDER, "Smartwaiver")],
        ondelete={PROVIDER: "cascade"},
    )

    # ------------------------------------------------------------------
    # Config / client
    # ------------------------------------------------------------------

    @api.model
    def _smartwaiver_get_api_key(self):
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
    def _smartwaiver_sync_enabled(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_ENABLED, default="False")
            == "True"
        )

    @api.model
    def _smartwaiver_template_allowlist(self):
        raw = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_TEMPLATE_IDS, default="")
            or ""
        )
        return {part.strip() for part in raw.split(",") if part.strip()}

    @api.model
    def _smartwaiver_get_client(self):
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_BASE_URL, default="")
            .strip()
            or None
        )
        return SmartwaiverClient(
            api_key=self._smartwaiver_get_api_key(),
            base_url=base_url,
        )

    # ------------------------------------------------------------------
    # Payload mapping → generic upsert
    # ------------------------------------------------------------------

    @api.model
    def _smartwaiver_vals_from_payload(self, payload):
        email = payload.get("email") or ""
        first = payload.get("firstName") or ""
        last = payload.get("lastName") or ""
        expiration_raw = payload.get("expirationDate") or ""
        expiration_date = False
        if expiration_raw:
            parsed = _parse_smartwaiver_dt(expiration_raw)
            expiration_date = parsed.date() if parsed else False

        return {
            "template_ref": payload.get("templateId")
            or payload.get("template_id")
            or False,
            "title": payload.get("title") or False,
            "created_on": _parse_smartwaiver_dt(
                payload.get("createdOn") or payload.get("created_on")
            ),
            "expiration_date": expiration_date,
            "expired": bool(payload.get("expired")),
            "verified": bool(payload.get("verified")),
            "kiosk": bool(payload.get("kiosk")),
            "email": email or False,
            "first_name": first or False,
            "middle_name": payload.get("middleName") or False,
            "last_name": last or False,
            "participant_payload": payload.get("participants") or [],
            "custom_fields": payload.get("customWaiverFields")
            or payload.get("custom_fields")
            or {},
            "raw_payload": {
                "waiverId": payload.get("waiverId"),
                "templateId": payload.get("templateId"),
                "email": email,
                "firstName": first,
                "lastName": last,
                "tags": payload.get("tags") or [],
            },
        }

    @api.model
    def _smartwaiver_upsert_from_payload(self, payload, auto_match=True):
        external_id = payload.get("waiverId") or payload.get("waiver_id")
        if not external_id:
            raise UserError(_("Smartwaiver payload is missing waiverId."))

        vals = self._smartwaiver_vals_from_payload(payload)
        allowlist = self._smartwaiver_template_allowlist()
        template_ref = vals.get("template_ref") or ""
        if allowlist and template_ref and template_ref not in allowlist:
            _logger.info(
                "Skipping Smartwaiver waiver %s (template %s not in allowlist)",
                external_id,
                template_ref,
            )
            return self.browse()

        return self.upsert_provider_waiver(
            PROVIDER,
            external_id,
            vals,
            auto_match=auto_match,
        )

    # ------------------------------------------------------------------
    # Provider hooks
    # ------------------------------------------------------------------

    def _provider_fetch_pdf(self):
        self.ensure_one()
        if self.provider != PROVIDER:
            return super()._provider_fetch_pdf()

        client = self._smartwaiver_get_client()
        try:
            detail = client.get_waiver(self.external_id, pdf=True)
        except SmartwaiverAPIError as exc:
            raise UserError(_("Smartwaiver PDF fetch failed: %s") % exc) from exc

        pdf_b64 = detail.get("pdf")
        if not pdf_b64:
            raise UserError(
                _("Smartwaiver did not return a PDF for waiver %s.") % self.external_id
            )

        pdf_bytes = base64.b64decode(pdf_b64)
        pdf_stored = base64.b64encode(pdf_bytes)
        name = f"smartwaiver-{self.external_id}.pdf"
        Attachment = self.env["ir.attachment"].sudo()
        if self.pdf_attachment_id:
            self.pdf_attachment_id.write(
                {
                    "name": name,
                    "datas": pdf_stored,
                    "mimetype": "application/pdf",
                }
            )
        else:
            attachment = Attachment.create(
                {
                    "name": name,
                    "type": "binary",
                    "datas": pdf_stored,
                    "res_model": self._name,
                    "res_id": self.id,
                    "mimetype": "application/pdf",
                }
            )
            self.pdf_attachment_id = attachment.id

        self._smartwaiver_upsert_from_payload(detail, auto_match=False)
        return True

    @api.model
    def _provider_search_and_import_for_partner(self, partner):
        imported = super()._provider_search_and_import_for_partner(partner)
        if not self._smartwaiver_get_api_key():
            return imported
        return imported | self._smartwaiver_search_and_import_for_partner(partner)

    @api.model
    def _smartwaiver_search_and_import_for_partner(self, partner):
        partner.ensure_one()
        client = self._smartwaiver_get_client()
        imported = self.browse()
        guids = []
        email = normalize_email(partner.email)
        if email:
            try:
                guids.append(client.search(email=email))
            except SmartwaiverAPIError as exc:
                raise UserError(_("Smartwaiver search failed: %s") % exc) from exc
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
                    imported |= self._smartwaiver_upsert_from_payload(payload)
                page += 1
        return imported

    # ------------------------------------------------------------------
    # Sync jobs
    # ------------------------------------------------------------------

    @api.model
    def cron_smartwaiver_poll_waivers(self, limit=50):
        if not self._smartwaiver_sync_enabled():
            _logger.debug("Smartwaiver sync disabled; skipping poll.")
            return False
        try:
            client = self._smartwaiver_get_client()
        except SmartwaiverAPIError as exc:
            _logger.warning("Smartwaiver poll skipped: %s", exc)
            return False

        ICP = self.env["ir.config_parameter"].sudo()
        from_dts = ICP.get_param(PARAM_LAST_POLL_AT, default="") or ""
        allowlist = self._smartwaiver_template_allowlist()
        template_id = next(iter(allowlist)) if len(allowlist) == 1 else ""

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
                self._smartwaiver_upsert_from_payload(summary)
                continue
            self._smartwaiver_upsert_from_payload(detail or summary)
            created = (detail or {}).get("createdOn") or summary.get("createdOn") or ""
            if created and (not newest or created > newest):
                newest = created

        if newest:
            ICP.set_param(PARAM_LAST_POLL_AT, newest)
        return True

    @api.model
    def action_smartwaiver_sync_now(self):
        if not self._smartwaiver_get_api_key():
            raise UserError(
                _(
                    "Configure a Smartwaiver API key in Settings or "
                    "SMARTWAIVER_API_KEY before syncing."
                )
            )
        self.env["ir.config_parameter"].sudo().set_param(PARAM_ENABLED, "True")
        self.cron_smartwaiver_poll_waivers()
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
    def cron_smartwaiver_drain_webhook_queue(self, max_messages=25):
        if not self._smartwaiver_sync_enabled():
            return False
        try:
            client = self._smartwaiver_get_client()
        except SmartwaiverAPIError as exc:
            _logger.warning("Smartwaiver webhook drain skipped: %s", exc)
            return False

        processed = 0
        for _ in range(max_messages):
            try:
                message = client.get_webhook_queue_account_message(delete=False)
            except SmartwaiverAPIError as exc:
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
                    self._smartwaiver_upsert_from_payload(detail)
                except SmartwaiverAPIError as exc:
                    _logger.warning(
                        "Smartwaiver webhook waiver %s fetch failed: %s",
                        waiver_id,
                        exc,
                    )
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
