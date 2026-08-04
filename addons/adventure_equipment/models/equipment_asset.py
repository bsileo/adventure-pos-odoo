# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

LIFECYCLE_TRANSITIONS = {
    "draft": {"active", "retired", "disposed"},
    "active": {
        "in_service",
        "out_for_service",
        "loaned",
        "transferred",
        "lost",
        "stolen",
        "retired",
        "disposed",
    },
    "in_service": {
        "active",
        "out_for_service",
        "loaned",
        "lost",
        "stolen",
        "retired",
        "disposed",
    },
    "out_for_service": {"active", "in_service", "retired", "disposed"},
    "loaned": {"active", "lost", "stolen", "transferred"},
    "transferred": set(),
    "lost": {"active", "retired", "disposed"},
    "stolen": {"retired", "disposed"},
    "retired": {"active", "disposed"},
    "disposed": set(),
}

WARRANTY_EXPIRING_SOON_DAYS = 30


class AdventureEquipmentAsset(models.Model):
    _name = "adventure.equipment.asset"
    _description = "Customer Equipment Asset"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _order = "name desc, id desc"
    _rec_name = "display_name"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    name = fields.Char(
        string="Equipment Number",
        required=True,
        copy=False,
        default=lambda self: _("New"),
        tracking=True,
        index=True,
    )
    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
        index=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    nickname = fields.Char(tracking=True)
    description = fields.Html()
    customer_note = fields.Text(
        help="Notes visible to the customer when portal access is enabled.",
    )
    internal_note = fields.Text(
        groups="adventure_equipment.group_equipment_user",
        help="Staff-only operational notes.",
    )
    payload = fields.Json(
        default=dict,
        help="Extension hook for sport-specific attributes until promoted to fields.",
    )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    category_id = fields.Many2one(
        "adventure.equipment.category",
        string="Category",
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    tag_ids = fields.Many2many(
        "adventure.equipment.tag",
        string="Tags",
    )

    # ------------------------------------------------------------------
    # Catalog link (optional; history survives catalog changes)
    # ------------------------------------------------------------------

    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product Template",
        ondelete="set null",
        index=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product Variant",
        ondelete="set null",
        tracking=True,
        index=True,
    )
    brand_name = fields.Char(tracking=True)
    manufacturer_name = fields.Char(tracking=True)
    model_name = fields.Char(tracking=True)
    manufacturer_sku = fields.Char(string="Manufacturer SKU", tracking=True)
    barcode = fields.Char(tracking=True)

    snapshot_product_name = fields.Char(string="Snapshot Product Name")
    snapshot_brand = fields.Char(string="Snapshot Brand")
    snapshot_manufacturer = fields.Char(string="Snapshot Manufacturer")
    snapshot_model = fields.Char(string="Snapshot Model")
    snapshot_sku = fields.Char(string="Snapshot SKU")
    snapshot_category = fields.Char(string="Snapshot Category")

    # ------------------------------------------------------------------
    # Identifiers
    # ------------------------------------------------------------------

    serial_number = fields.Char(tracking=True, index=True)
    asset_tag = fields.Char(string="Shop Asset Tag", tracking=True)
    manufacturer_registration = fields.Char(tracking=True)
    identifier_ids = fields.One2many(
        "adventure.equipment.identifier",
        "asset_id",
        string="Identifiers",
    )

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------

    partner_id = fields.Many2one(
        "res.partner",
        string="Current Owner",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    ownership_type = fields.Selection(
        [
            ("customer", "Customer"),
            ("organization", "Organization"),
            ("shop", "Shop"),
        ],
        string="Ownership Type",
        default="customer",
        required=True,
        tracking=True,
    )
    ownership_verification_state = fields.Selection(
        [
            ("unverified", "Unverified"),
            ("pending", "Pending Verification"),
            ("verified", "Verified"),
            ("disputed", "Disputed"),
        ],
        string="Ownership Verification",
        default="unverified",
        tracking=True,
    )
    ownership_start_date = fields.Date(tracking=True)
    acquired_on = fields.Date(string="Acquired On", tracking=True)
    ownership_ids = fields.One2many(
        "adventure.equipment.ownership",
        "asset_id",
        string="Ownership History",
    )

    # ------------------------------------------------------------------
    # Acquisition / provenance
    # ------------------------------------------------------------------

    acquisition_source = fields.Selection(
        [
            ("shop_sale", "Sold by This Shop"),
            ("other_shop", "Other Shop"),
            ("manufacturer", "Manufacturer"),
            ("used", "Used / Pre-owned"),
            ("gift", "Gift"),
            ("migration", "Data Migration"),
            ("unknown", "Unknown"),
            ("customer_reported", "Customer Reported"),
            ("manual_shop", "Manual Shop Entry"),
        ],
        string="Acquisition Source",
        default="unknown",
        tracking=True,
    )
    sold_by_this_shop = fields.Boolean(
        compute="_compute_sold_by_this_shop",
        store=True,
    )
    original_seller = fields.Char()
    purchase_date = fields.Date()
    purchase_price = fields.Monetary(
        groups="adventure_equipment.group_equipment_manager",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    origin_sale_ref = fields.Char(
        string="Origin Sale Reference",
        help="Human-readable reference to the originating sale (order name, receipt, etc.).",
    )
    source_record_ref = fields.Char(
        string="Source Record Reference",
        help="Technical reference to the originating record when available.",
    )
    data_provenance = fields.Char(
        help="Where this record's data originated (import job, connector, manual entry, etc.).",
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    lifecycle_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("in_service", "In Service"),
            ("out_for_service", "Out for Service"),
            ("loaned", "Loaned"),
            ("transferred", "Transferred"),
            ("lost", "Lost"),
            ("stolen", "Stolen"),
            ("retired", "Retired"),
            ("disposed", "Disposed"),
        ],
        string="Lifecycle State",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    in_service_date = fields.Date()
    retired_on = fields.Date(tracking=True)
    retirement_reason = fields.Text()
    lost_on = fields.Date(tracking=True)
    disposition_on = fields.Date()
    lifecycle_notes = fields.Text()

    # ------------------------------------------------------------------
    # Condition
    # ------------------------------------------------------------------

    condition_state = fields.Selection(
        [
            ("new", "New"),
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
            ("unknown", "Unknown"),
        ],
        string="Condition",
        default="unknown",
        required=True,
        tracking=True,
    )
    condition_notes = fields.Text()
    condition_assessed_on = fields.Date()
    condition_assessed_by = fields.Many2one("res.users", string="Assessed By")
    condition_customer_reported = fields.Boolean(
        string="Customer Reported Condition",
        help="Condition was reported by the customer rather than assessed by staff.",
    )
    last_verified_on = fields.Date(string="Last Verified On")

    # ------------------------------------------------------------------
    # Warranty
    # ------------------------------------------------------------------

    warranty_registered = fields.Boolean(string="Warranty Registered")
    warranty_lifetime = fields.Boolean(string="Lifetime Warranty")
    warranty_not_applicable = fields.Boolean(string="Warranty Not Applicable")
    warranty_start_date = fields.Date()
    warranty_end_date = fields.Date(tracking=True)
    warranty_registration_number = fields.Char()
    warranty_provider = fields.Char()
    warranty_notes = fields.Text()
    warranty_status = fields.Selection(
        [
            ("unknown", "Unknown"),
            ("not_registered", "Not Registered"),
            ("active", "Active"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
            ("lifetime", "Lifetime"),
            ("not_applicable", "Not Applicable"),
        ],
        string="Warranty Status",
        compute="_compute_warranty_status",
        store=True,
    )

    # ------------------------------------------------------------------
    # Documents & timeline
    # ------------------------------------------------------------------

    document_ids = fields.One2many(
        "adventure.equipment.document",
        "asset_id",
        string="Documents",
    )
    event_ids = fields.One2many(
        "adventure.equipment.event",
        "asset_id",
        string="Events",
    )
    document_count = fields.Integer(compute="_compute_document_count")

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "Equipment number must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends("name", "nickname", "brand_name", "model_name", "serial_number")
    def _compute_display_name(self):
        for asset in self:
            label_parts = []
            if asset.nickname:
                label_parts.append(asset.nickname)
            else:
                identity = " ".join(
                    part for part in (asset.brand_name, asset.model_name) if part
                ).strip()
                if identity:
                    label_parts.append(identity)
            if asset.serial_number:
                label_parts.append(f"({asset.serial_number})")
            if asset.name and asset.name != _("New"):
                label_parts.append(f"[{asset.name}]")
            elif not label_parts:
                label_parts.append(asset.name or _("Equipment"))
            asset.display_name = " ".join(label_parts)

    @api.depends("acquisition_source")
    def _compute_sold_by_this_shop(self):
        for asset in self:
            asset.sold_by_this_shop = asset.acquisition_source == "shop_sale"

    @api.depends(
        "warranty_registered",
        "warranty_lifetime",
        "warranty_not_applicable",
        "warranty_start_date",
        "warranty_end_date",
    )
    def _compute_warranty_status(self):
        today = fields.Date.context_today(self)
        for asset in self:
            if asset.warranty_not_applicable:
                asset.warranty_status = "not_applicable"
            elif asset.warranty_lifetime:
                asset.warranty_status = "lifetime"
            elif not asset.warranty_registered:
                asset.warranty_status = "not_registered"
            elif asset.warranty_end_date:
                if asset.warranty_end_date < today:
                    asset.warranty_status = "expired"
                elif asset.warranty_end_date <= today + timedelta(
                    days=WARRANTY_EXPIRING_SOON_DAYS
                ):
                    asset.warranty_status = "expiring_soon"
                else:
                    asset.warranty_status = "active"
            elif asset.warranty_start_date:
                asset.warranty_status = "active"
            else:
                asset.warranty_status = "unknown"

    @api.depends("document_ids")
    def _compute_document_count(self):
        for asset in self:
            asset.document_count = len(asset.document_ids)

    # ------------------------------------------------------------------
    # Product defaults
    # ------------------------------------------------------------------

    def _product_brand_name(self, product):
        template = product.product_tmpl_id if product else self.env["product.template"]
        for record in (product, template):
            if not record:
                continue
            for field_name in ("brand_name", "product_brand_id"):
                if field_name in record._fields:
                    value = record[field_name]
                    if field_name.endswith("_id") and value:
                        return value.display_name
                    if value:
                        return value
        return False

    def _product_manufacturer_name(self, product):
        template = product.product_tmpl_id if product else self.env["product.template"]
        for record in (product, template):
            if not record:
                continue
            if "manufacturer_name" in record._fields and record.manufacturer_name:
                return record.manufacturer_name
        return False

    def _product_model_name(self, product):
        template = product.product_tmpl_id if product else self.env["product.template"]
        for record in (product, template):
            if not record:
                continue
            for field_name in ("model_name", "default_code"):
                if field_name in record._fields and record[field_name]:
                    return record[field_name]
        return False

    def _snapshot_category_name(self, asset):
        if asset.category_id:
            return asset.category_id.display_name
        if asset.product_id and asset.product_id.categ_id:
            return asset.product_id.categ_id.display_name
        if asset.product_tmpl_id and asset.product_tmpl_id.categ_id:
            return asset.product_tmpl_id.categ_id.display_name
        return False

    def _apply_product_defaults(self, overwrite=False):
        for asset in self:
            product = asset.product_id
            if not product:
                continue
            template = product.product_tmpl_id
            vals = {}
            if overwrite or not asset.product_tmpl_id:
                vals["product_tmpl_id"] = template.id
            if overwrite or not asset.brand_name:
                brand = asset._product_brand_name(product)
                if brand:
                    vals["brand_name"] = brand
            if overwrite or not asset.manufacturer_name:
                manufacturer = asset._product_manufacturer_name(product)
                if manufacturer:
                    vals["manufacturer_name"] = manufacturer
            if overwrite or not asset.model_name:
                model = asset._product_model_name(product)
                if model:
                    vals["model_name"] = model
            if overwrite or not asset.manufacturer_sku:
                sku = product.default_code or template.default_code
                if sku:
                    vals["manufacturer_sku"] = sku
            if overwrite or not asset.barcode:
                barcode = product.barcode or template.barcode
                if barcode:
                    vals["barcode"] = barcode
            if overwrite or not asset.snapshot_product_name:
                vals["snapshot_product_name"] = product.display_name
            if overwrite or not asset.snapshot_brand:
                brand = vals.get("brand_name") or asset.brand_name
                if brand:
                    vals["snapshot_brand"] = brand
            if overwrite or not asset.snapshot_manufacturer:
                manufacturer = vals.get("manufacturer_name") or asset.manufacturer_name
                if manufacturer:
                    vals["snapshot_manufacturer"] = manufacturer
            if overwrite or not asset.snapshot_model:
                model = vals.get("model_name") or asset.model_name
                if model:
                    vals["snapshot_model"] = model
            if overwrite or not asset.snapshot_sku:
                sku = vals.get("manufacturer_sku") or asset.manufacturer_sku
                if sku:
                    vals["snapshot_sku"] = sku
            if overwrite or not asset.snapshot_category:
                category_name = asset._snapshot_category_name(asset)
                if category_name:
                    vals["snapshot_category"] = category_name
            if vals:
                asset.write(vals)

    def action_refresh_product_defaults(self):
        self._apply_product_defaults(overwrite=True)
        return True

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if not self.product_id:
            return
        product = self.product_id
        template = product.product_tmpl_id
        if not self.product_tmpl_id:
            self.product_tmpl_id = template
        if not self.brand_name:
            self.brand_name = self._product_brand_name(product)
        if not self.manufacturer_name:
            self.manufacturer_name = self._product_manufacturer_name(product)
        if not self.model_name:
            self.model_name = self._product_model_name(product)
        if not self.manufacturer_sku:
            self.manufacturer_sku = product.default_code or template.default_code
        if not self.barcode:
            self.barcode = product.barcode or template.barcode

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def _check_lifecycle_transition(self, previous_state, new_state):
        if previous_state == new_state:
            return
        allowed = LIFECYCLE_TRANSITIONS.get(previous_state, set())
        if new_state not in allowed:
            raise UserError(
                _(
                    "Cannot change lifecycle state from '%(old)s' to '%(new)s'.",
                    old=dict(self._fields["lifecycle_state"].selection).get(previous_state),
                    new=dict(self._fields["lifecycle_state"].selection).get(new_state),
                )
            )

    def _log_event(self, event_type, summary, extra_vals=None):
        Event = self.env["adventure.equipment.event"]
        for asset in self:
            vals = {
                "asset_id": asset.id,
                "event_type": event_type,
                "summary": summary,
                "company_id": asset.company_id.id,
            }
            if extra_vals:
                vals.update(extra_vals)
            Event.create(vals)

    def _sync_ownership_history_after_partner_change(self, transfer_date=None):
        Ownership = self.env["adventure.equipment.ownership"]
        transfer_date = transfer_date or fields.Date.context_today(self)
        for asset in self:
            Ownership._transfer_ownership(
                asset,
                asset.partner_id,
                transfer_date,
                change_type="transfer",
                verification_state=asset.ownership_verification_state,
            )

    def _ensure_primary_serial_identifier(self):
        Identifier = self.env["adventure.equipment.identifier"]
        for asset in self:
            if not asset.serial_number:
                continue
            primary = asset.identifier_ids.filtered(
                lambda row: row.id_type == "serial" and row.primary
            )
            if primary:
                primary[:1].write({"name": asset.serial_number})
            else:
                Identifier.create(
                    {
                        "asset_id": asset.id,
                        "id_type": "serial",
                        "name": asset.serial_number,
                        "primary": True,
                        "company_id": asset.company_id.id,
                    }
                )

    def _create_initial_ownership(self):
        Ownership = self.env["adventure.equipment.ownership"]
        for asset in self:
            Ownership.create(
                {
                    "asset_id": asset.id,
                    "partner_id": asset.partner_id.id,
                    "date_from": asset.ownership_start_date or fields.Date.context_today(asset),
                    "change_type": "registration",
                    "is_current": True,
                    "verification_state": asset.ownership_verification_state,
                    "company_id": asset.company_id.id,
                }
            )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            name = vals.get("name") or _("New")
            if name in (_("New"), "New"):
                vals["name"] = (
                    sequence.next_by_code("adventure.equipment.asset") or _("New")
                )
            if vals.get("product_id") and not vals.get("product_tmpl_id"):
                product = self.env["product.product"].browse(vals["product_id"])
                vals["product_tmpl_id"] = product.product_tmpl_id.id
            if not vals.get("ownership_start_date"):
                vals["ownership_start_date"] = fields.Date.context_today(self)
        assets = super().create(vals_list)
        assets._apply_product_defaults(overwrite=False)
        assets._ensure_primary_serial_identifier()
        assets._create_initial_ownership()
        assets._log_event("registered", _("Equipment registered"))
        return assets

    def write(self, vals):
        if (
            "lifecycle_state" in vals
            and not self.env.context.get("equipment_skip_lifecycle_check")
        ):
            new_state = vals["lifecycle_state"]
            for asset in self:
                asset._check_lifecycle_transition(asset.lifecycle_state, new_state)
        if vals.get("product_id") and not vals.get("product_tmpl_id"):
            product = self.env["product.product"].browse(vals["product_id"])
            vals["product_tmpl_id"] = product.product_tmpl_id.id
        result = super().write(vals)
        if "serial_number" in vals:
            self._ensure_primary_serial_identifier()
        if (
            "partner_id" in vals
            and not self.env.context.get("equipment_skip_ownership_sync")
        ):
            self._sync_ownership_history_after_partner_change(
                transfer_date=vals.get("ownership_start_date")
            )
        return result

    def unlink(self):
        for asset in self:
            if asset.lifecycle_state != "draft":
                raise UserError(
                    _(
                        "Only draft equipment records without history can be deleted. "
                        "Archive or retire this equipment instead."
                    )
                )
            if asset.document_ids:
                raise UserError(
                    _(
                        "Equipment with documents cannot be deleted. "
                        "Archive or retire this equipment instead."
                    )
                )
            if len(asset.ownership_ids) > 1:
                raise UserError(
                    _(
                        "Equipment with ownership history cannot be deleted. "
                        "Archive or retire this equipment instead."
                    )
                )
            if len(asset.event_ids) > 1:
                raise UserError(
                    _(
                        "Equipment with event history cannot be deleted. "
                        "Archive or retire this equipment instead."
                    )
                )
        return super().unlink()

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains("warranty_start_date", "warranty_end_date")
    def _check_warranty_dates(self):
        for asset in self:
            if (
                asset.warranty_start_date
                and asset.warranty_end_date
                and asset.warranty_end_date < asset.warranty_start_date
            ):
                raise ValidationError(
                    _("Warranty end date must be on or after the start date.")
                )

    @api.constrains("product_id", "product_tmpl_id")
    def _check_product_consistency(self):
        for asset in self:
            if (
                asset.product_id
                and asset.product_tmpl_id
                and asset.product_id.product_tmpl_id != asset.product_tmpl_id
            ):
                raise ValidationError(
                    _(
                        "The selected product variant does not belong to the selected product template."
                    )
                )

    @api.constrains("partner_id", "company_id")
    def _check_partner_company(self):
        for asset in self:
            partner_company = asset.partner_id.company_id
            if partner_company and partner_company != asset.company_id:
                raise ValidationError(
                    _(
                        "The current owner must belong to the same company as the equipment record."
                    )
                )

    @api.constrains("serial_number", "company_id", "brand_name", "model_name")
    def _check_serial_soft_unique(self):
        if self.env.context.get("equipment_allow_duplicate_serial"):
            return
        for asset in self:
            serial = (asset.serial_number or "").strip()
            if not serial:
                continue
            domain = [
                ("id", "!=", asset.id),
                ("company_id", "=", asset.company_id.id),
                ("serial_number", "=ilike", serial),
            ]
            if (asset.brand_name or "").strip():
                domain.append(("brand_name", "=ilike", asset.brand_name.strip()))
            if (asset.model_name or "").strip():
                domain.append(("model_name", "=ilike", asset.model_name.strip()))
            if self.search_count(domain):
                raise ValidationError(
                    _(
                        "A piece of equipment with this serial number already exists "
                        "for this brand and model in your company."
                    )
                )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_activate(self):
        today = fields.Date.context_today(self)
        to_activate = self.filtered(lambda asset: asset.lifecycle_state != "active")
        if not to_activate:
            return True
        without_in_service = to_activate.filtered(lambda asset: not asset.in_service_date)
        if without_in_service:
            without_in_service.write(
                {"lifecycle_state": "active", "in_service_date": today}
            )
        (to_activate - without_in_service).write({"lifecycle_state": "active"})
        to_activate._log_event(
            "lifecycle_changed",
            _("Equipment activated"),
            {"payload": {"lifecycle_state": "active"}},
        )
        return True

    def action_mark_out_for_service(self):
        self.write({"lifecycle_state": "out_for_service"})
        self._log_event(
            "lifecycle_changed",
            _("Marked out for service"),
            {"payload": {"lifecycle_state": "out_for_service"}},
        )
        return True

    def action_mark_returned_from_service(self):
        self.write({"lifecycle_state": "active"})
        self._log_event(
            "lifecycle_changed",
            _("Returned from service"),
            {"payload": {"lifecycle_state": "active"}},
        )
        return True

    def action_retire(self):
        today = fields.Date.context_today(self)
        self.write({"lifecycle_state": "retired", "retired_on": today})
        self._log_event(
            "retired",
            _("Equipment retired"),
            {"payload": {"lifecycle_state": "retired", "retired_on": str(today)}},
        )
        return True

    def action_mark_lost(self):
        today = fields.Date.context_today(self)
        self.write({"lifecycle_state": "lost", "lost_on": today})
        self._log_event(
            "lifecycle_changed",
            _("Equipment marked as lost"),
            {"payload": {"lifecycle_state": "lost", "lost_on": str(today)}},
        )
        return True

    def action_reactivate(self):
        self.write({"lifecycle_state": "active"})
        self._log_event("reactivated", _("Equipment reactivated"))
        return True

    def action_open_transfer_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Transfer Ownership"),
            "res_model": "adventure.equipment.ownership.transfer.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_asset_id": self.id,
                "default_from_partner_id": self.partner_id.id,
                "default_transfer_date": fields.Date.context_today(self),
                "default_verification_state": self.ownership_verification_state,
            },
        }
