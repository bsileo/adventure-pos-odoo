# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AdventureEquipmentOwnership(models.Model):
    _name = "adventure.equipment.ownership"
    _description = "Equipment Ownership History"
    _order = "is_current desc, date_from desc, id desc"

    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        string="Equipment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        ondelete="restrict",
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )
    date_from = fields.Date(required=True, index=True)
    date_to = fields.Date(index=True)
    change_type = fields.Selection(
        [
            ("registration", "Registration"),
            ("sale", "Sale"),
            ("transfer", "Transfer"),
            ("correction", "Correction"),
            ("migration", "Migration"),
        ],
        string="Change Type",
        required=True,
        default="registration",
        index=True,
    )
    is_current = fields.Boolean(
        string="Current",
        default=False,
        index=True,
    )
    verification_state = fields.Selection(
        [
            ("unverified", "Unverified"),
            ("pending", "Pending Verification"),
            ("verified", "Verified"),
            ("disputed", "Disputed"),
        ],
        string="Verification State",
        default="unverified",
        index=True,
    )
    notes = fields.Text()
    source_transaction_ref = fields.Char(
        string="Source Transaction Reference",
        help="Human-readable reference to the sale, transfer, or import that created this row.",
    )

    @api.constrains("date_from", "date_to")
    def _check_ownership_dates(self):
        for ownership in self:
            if (
                ownership.date_from
                and ownership.date_to
                and ownership.date_to < ownership.date_from
            ):
                raise ValidationError(
                    _("Ownership end date must be on or after the start date.")
                )

    @api.constrains("asset_id", "is_current")
    def _check_single_current_owner(self):
        for ownership in self:
            if not ownership.is_current:
                continue
            duplicate_count = self.search_count(
                [
                    ("id", "!=", ownership.id),
                    ("asset_id", "=", ownership.asset_id.id),
                    ("is_current", "=", True),
                ]
            )
            if duplicate_count:
                raise ValidationError(
                    _("Only one current ownership row is allowed per equipment record.")
                )

    def _close_current(self, close_date):
        self.ensure_one()
        vals = {"is_current": False}
        if close_date:
            vals["date_to"] = close_date
        self.write(vals)
        return True

    @api.model
    def _transfer_ownership(
        self,
        asset,
        new_partner,
        transfer_date,
        change_type="transfer",
        verification_state=None,
        notes=None,
        source_transaction_ref=None,
    ):
        """Close the current ownership row and open a new current row for *asset*."""
        transfer_date = transfer_date or fields.Date.context_today(self)
        current = asset.ownership_ids.filtered("is_current")
        if current:
            current._close_current(transfer_date)

        return self.create(
            {
                "asset_id": asset.id,
                "partner_id": new_partner.id,
                "date_from": transfer_date,
                "change_type": change_type,
                "is_current": True,
                "verification_state": verification_state or asset.ownership_verification_state,
                "notes": notes,
                "source_transaction_ref": source_transaction_ref,
                "company_id": asset.company_id.id,
            }
        )
