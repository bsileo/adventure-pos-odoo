# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AdventureEquipmentDocument(models.Model):
    _name = "adventure.equipment.document"
    _description = "Equipment Document"
    _order = "issue_date desc, name, id desc"

    asset_id = fields.Many2one(
        "adventure.equipment.asset",
        string="Equipment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(required=True)
    document_type = fields.Selection(
        [
            ("image", "Image"),
            ("receipt", "Receipt"),
            ("warranty", "Warranty"),
            ("manual", "Manual"),
            ("certification", "Certification"),
            ("inspection", "Inspection"),
            ("other", "Other"),
        ],
        string="Document Type",
        required=True,
        default="other",
        index=True,
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Attachment",
        ondelete="set null",
        index=True,
    )
    issue_date = fields.Date(index=True)
    expiration_date = fields.Date(index=True)
    issuer = fields.Char()
    customer_visible = fields.Boolean(
        string="Visible to Customer",
        default=False,
    )
    verified = fields.Boolean(default=False)
    notes = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        documents = super().create(vals_list)
        documents._link_attachments_to_asset()
        return documents

    def _link_attachments_to_asset(self):
        for document in self:
            attachment = document.attachment_id
            if not attachment:
                continue
            if attachment.res_model and attachment.res_id:
                continue
            attachment.write(
                {
                    "res_model": "adventure.equipment.asset",
                    "res_id": document.asset_id.id,
                }
            )
