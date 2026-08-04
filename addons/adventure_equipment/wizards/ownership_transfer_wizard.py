# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AdventureEquipmentOwnershipTransferWizard(models.TransientModel):
    _name = "adventure.equipment.ownership.transfer.wizard"
    _description = "Transfer Equipment Ownership"

    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        string="Equipment",
        required=True,
        ondelete="cascade",
    )
    from_partner_id = fields.Many2one(
        "res.partner",
        string="From",
        required=True,
        ondelete="restrict",
    )
    to_partner_id = fields.Many2one(
        "res.partner",
        string="To",
        required=True,
        ondelete="restrict",
    )
    transfer_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    reason = fields.Selection(
        [
            ("sale", "Sale"),
            ("transfer", "Transfer"),
            ("correction", "Correction"),
            ("migration", "Migration"),
        ],
        string="Reason",
        default="transfer",
        required=True,
    )
    notes = fields.Text()
    verification_state = fields.Selection(
        [
            ("unverified", "Unverified"),
            ("pending", "Pending Verification"),
            ("verified", "Verified"),
            ("disputed", "Disputed"),
        ],
        string="Verification State",
        default="unverified",
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="asset_id.company_id",
    )

    @api.onchange("asset_id")
    def _onchange_asset_id(self):
        if not self.asset_id:
            return
        self.from_partner_id = self.asset_id.partner_id
        self.verification_state = self.asset_id.ownership_verification_state

    def action_confirm(self):
        self.ensure_one()
        asset = self.asset_id
        if self.to_partner_id == self.from_partner_id:
            raise UserError(_("The new owner must be different from the current owner."))
        if asset.partner_id != self.from_partner_id:
            raise UserError(
                _(
                    "The equipment owner has changed since this wizard was opened. "
                    "Please close and reopen the transfer wizard."
                )
            )

        Ownership = self.env["adventure.equipment.ownership"]
        Ownership._transfer_ownership(
            asset,
            self.to_partner_id,
            self.transfer_date,
            change_type=self.reason,
            verification_state=self.verification_state,
            notes=self.notes,
        )

        asset.with_context(equipment_skip_ownership_sync=True).write(
            {
                "partner_id": self.to_partner_id.id,
                "ownership_start_date": self.transfer_date,
                "ownership_verification_state": self.verification_state,
            }
        )

        asset._log_event(
            "ownership_transferred",
            _("Ownership transferred from %(from)s to %(to)s.")
            % {
                "from": self.from_partner_id.display_name,
                "to": self.to_partner_id.display_name,
            },
            {
                "payload": {
                    "from_partner_id": self.from_partner_id.id,
                    "to_partner_id": self.to_partner_id.id,
                    "transfer_date": fields.Date.to_string(self.transfer_date),
                    "reason": self.reason,
                }
            },
        )

        return {"type": "ir.actions.act_window_close"}
