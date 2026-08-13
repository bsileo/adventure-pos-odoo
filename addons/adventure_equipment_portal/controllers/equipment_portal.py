# -*- coding: utf-8 -*-

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class EquipmentCustomerPortal(CustomerPortal):
    """Portal controllers for adventure.equipment.asset."""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "equipment_count" in counters:
            partner = request.env.user.partner_id
            values["equipment_count"] = request.env["adventure.equipment.asset"].search_count(
                [("partner_id", "=", partner.id)]
            )
        return values

    def _get_equipment_domain(self):
        return [("partner_id", "=", request.env.user.partner_id.id)]

    @http.route(
        ["/my/equipment", "/my/equipment/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_equipment(self, page=1, **kwargs):
        values = self._prepare_portal_layout_values()
        Equipment = request.env["adventure.equipment.asset"]
        domain = self._get_equipment_domain()
        total = Equipment.search_count(domain)
        pager_values = portal_pager(
            url="/my/equipment",
            total=total,
            page=page,
            step=self._items_per_page,
        )
        equipment = Equipment.search(
            domain,
            order="nickname, name, id desc",
            limit=self._items_per_page,
            offset=pager_values["offset"],
        )
        values.update(
            {
                "equipment_ids": equipment,
                "page_name": "equipment",
                "pager": pager_values,
                "default_url": "/my/equipment",
            }
        )
        return request.render("adventure_equipment_portal.portal_my_equipment", values)

    @http.route(
        ["/my/equipment/<int:equipment_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_equipment_detail(self, equipment_id, **kwargs):
        try:
            equipment = self._document_check_access(
                "adventure.equipment.asset", equipment_id
            )
        except (AccessError, MissingError):
            return request.redirect("/my/equipment")
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "equipment": equipment,
                "page_name": "equipment",
                "documents": equipment.document_ids.filtered("customer_visible"),
            }
        )
        return request.render(
            "adventure_equipment_portal.portal_my_equipment_detail", values
        )

    @http.route(
        ["/my/equipment/<int:equipment_id>/edit"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_my_equipment_edit(self, equipment_id, **post):
        try:
            equipment = self._document_check_access(
                "adventure.equipment.asset", equipment_id
            )
        except (AccessError, MissingError):
            return request.redirect("/my/equipment")

        error = False
        if request.httprequest.method == "POST":
            vals = {
                "nickname": (post.get("nickname") or "").strip() or False,
                "customer_note": (post.get("customer_note") or "").strip() or False,
            }
            try:
                equipment.write(vals)
                return request.redirect("/my/equipment/%s" % equipment.id)
            except AccessError:
                error = _("You are not allowed to update this equipment.")
            except Exception:
                error = _("Could not save your changes. Please try again.")

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "equipment": equipment,
                "page_name": "equipment",
                "error": error,
            }
        )
        return request.render(
            "adventure_equipment_portal.portal_my_equipment_edit", values
        )

    @http.route(
        ["/my/equipment/register"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_my_equipment_register(self, **post):
        Category = request.env["adventure.equipment.category"]
        categories = Category.search([("active", "=", True)], order="sequence, name")
        error = False

        if request.httprequest.method == "POST":
            nickname = (post.get("nickname") or "").strip()
            category_id = post.get("category_id")
            brand_name = (post.get("brand_name") or "").strip()
            model_name = (post.get("model_name") or "").strip()
            serial_number = (post.get("serial_number") or "").strip()
            customer_note = (post.get("customer_note") or "").strip()

            if not category_id:
                error = _("Please choose a category.")
            elif not (brand_name or model_name or nickname):
                error = _("Please provide at least a nickname, brand, or model.")
            else:
                vals = {
                    "partner_id": request.env.user.partner_id.id,
                    "company_id": request.env.company.id,
                    "category_id": int(category_id),
                    "nickname": nickname or False,
                    "brand_name": brand_name or False,
                    "model_name": model_name or False,
                    "serial_number": serial_number or False,
                    "customer_note": customer_note or False,
                    "acquisition_source": "customer_reported",
                    "ownership_verification_state": "pending",
                    "lifecycle_state": "draft",
                    "ownership_type": "customer",
                    "condition_state": "unknown",
                    "data_provenance": "portal_customer_registration",
                }
                try:
                    asset = request.env["adventure.equipment.asset"].create(vals)
                    return request.redirect("/my/equipment/%s" % asset.id)
                except AccessError:
                    error = _("You are not allowed to register equipment.")
                except Exception:
                    error = _(
                        "Could not register this equipment. "
                        "Check your details or contact the shop."
                    )

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "categories": categories,
                "page_name": "equipment",
                "error": error,
                "post": post,
            }
        )
        return request.render(
            "adventure_equipment_portal.portal_my_equipment_register", values
        )
