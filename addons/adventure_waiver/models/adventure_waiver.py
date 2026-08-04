# -*- coding: utf-8 -*-
"""Generic signed-waiver domain for Adventure POS.

Provider connectors (e.g. adventure_smartwaiver) inherit this model to:
- ``selection_add`` on ``provider``
- override ``_provider_fetch_pdf`` / ``_provider_search_and_import_for_partner``
- upsert via ``upsert_provider_waiver``

Do not put vendor API clients or vendor payload keys in this module.
"""

import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def normalize_email(value):
    if not value:
        return ""
    return value.strip().lower()


def normalize_name_part(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


class AdventureWaiver(models.Model):
    _name = "adventure.waiver"
    _description = "Signed waiver"
    _order = "created_on desc, id desc"
    _rec_name = "display_name"

    provider = fields.Selection(
        selection=[("manual", "Manual")],
        string="Provider",
        required=True,
        default="manual",
        index=True,
        help="Waiver source system. Provider modules extend this selection.",
    )
    external_id = fields.Char(
        string="External ID",
        required=True,
        index=True,
        copy=False,
        help="Immutable ID from the provider (or a local key for manual rows).",
    )
    template_ref = fields.Char(
        string="Template reference",
        index=True,
        help="Provider template / form identifier when applicable.",
    )
    title = fields.Char()
    created_on = fields.Datetime(index=True)
    expiration_date = fields.Date()
    expired = fields.Boolean(default=False, index=True)
    verified = fields.Boolean(default=False)
    kiosk = fields.Boolean(
        default=False,
        help="Signed at a kiosk or similar in-person capture, when the provider reports it.",
    )

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
    raw_payload = fields.Json(string="Provider payload fragment")
    last_sync_at = fields.Datetime()

    pdf_attachment_id = fields.Many2one(
        "ir.attachment",
        string="PDF",
        ondelete="set null",
        copy=False,
    )
    display_name = fields.Char(compute="_compute_display_name", store=True)

    _provider_external_uniq = models.Constraint(
        "UNIQUE(provider, external_id)",
        "External waiver ID must be unique per provider.",
    )

    @api.depends("title", "first_name", "last_name", "external_id", "provider")
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
                rec.display_name = rec.external_id or _("Waiver")

    # ------------------------------------------------------------------
    # Partner matching (provider-neutral)
    # ------------------------------------------------------------------

    @api.model
    def _partners_for_email(self, email):
        normalized = normalize_email(email)
        if not normalized:
            return self.env["res.partner"]
        partners = self.env["res.partner"].search([("email", "ilike", normalized)])
        return partners.filtered(lambda p: normalize_email(p.email) == normalized)

    @api.model
    def _partners_for_name(self, first_name, last_name):
        first = normalize_name_part(first_name)
        last = normalize_name_part(last_name)
        if not first or not last:
            return self.env["res.partner"]
        domain = [
            ("name", "ilike", first),
            ("name", "ilike", last),
        ]
        candidates = self.env["res.partner"].search(domain, limit=50)
        exact = self.env["res.partner"]
        for partner in candidates:
            parts = normalize_name_part(partner.name).split(" ")
            if len(parts) >= 2 and parts[0] == first and parts[-1] == last:
                exact |= partner
            elif (
                normalize_name_part(getattr(partner, "firstname", "") or "") == first
                and normalize_name_part(getattr(partner, "lastname", "") or "") == last
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
        normalized = normalize_email(email)
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
            "res_model": "adventure.waiver.link.wizard",
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
    # Provider extension hooks
    # ------------------------------------------------------------------

    def action_fetch_pdf(self):
        """Fetch PDF via the provider hook for each record."""
        for waiver in self:
            waiver._provider_fetch_pdf()
        return True

    def _provider_fetch_pdf(self):
        """Provider modules override for their ``provider`` value."""
        self.ensure_one()
        raise UserError(
            _("PDF fetch is not available for provider '%s'.") % (self.provider,)
        )

    @api.model
    def _provider_search_and_import_for_partner(self, partner):
        """Extension hook: providers append imported waivers for this partner.

        Generic core returns an empty recordset. Installed provider modules
        override and call ``super()`` then union their results.
        """
        partner.ensure_one()
        return self.browse()

    # ------------------------------------------------------------------
    # Idempotent upsert (used by providers)
    # ------------------------------------------------------------------

    @api.model
    def upsert_provider_waiver(self, provider, external_id, vals, auto_match=True):
        """Create or update a waiver for ``(provider, external_id)``.

        ``vals`` must not need to include provider/external_id (they are set here).
        Manual match links are preserved on update.
        """
        if not provider:
            raise UserError(_("Provider is required to upsert a waiver."))
        if not external_id:
            raise UserError(_("External ID is required to upsert a waiver."))

        write_vals = dict(vals or {})
        write_vals["provider"] = provider
        write_vals["external_id"] = external_id
        if write_vals.get("email"):
            write_vals["email_normalized"] = normalize_email(write_vals["email"]) or False
        first = write_vals.get("first_name") or ""
        last = write_vals.get("last_name") or ""
        if first or last:
            write_vals["name_normalized"] = (
                f"{normalize_name_part(first)} {normalize_name_part(last)}".strip()
                or False
            )
        write_vals.setdefault("last_sync_at", fields.Datetime.now())

        existing = self.search(
            [("provider", "=", provider), ("external_id", "=", external_id)],
            limit=1,
        )
        if existing:
            if existing.match_state == "manual":
                write_vals.pop("partner_id", None)
            existing.write(write_vals)
            record = existing
        else:
            record = self.create(write_vals)

        if auto_match and record.match_state != "manual":
            record._apply_auto_match()
        return record
