# -*- coding: utf-8 -*-

from odoo import _, http
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class EquipmentConfigurationCustomerPortal(CustomerPortal):
    """Portal controllers for packing lists and configurations."""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "equipment_list_count" in counters:
            partner = request.env.user.partner_id
            values["equipment_list_count"] = request.env[
                "adventure.equipment.configuration"
            ].search_count([("partner_id", "=", partner.id)])
        return values

    def _get_list_domain(self, list_kind=None):
        domain = [("partner_id", "=", request.env.user.partner_id.id)]
        if list_kind in ("packing", "configuration"):
            domain.append(("list_kind", "=", list_kind))
        return domain

    def _get_owned_assets(self):
        return request.env["adventure.equipment.asset"].search(
            [("partner_id", "=", request.env.user.partner_id.id)],
            order="nickname, name, id desc",
        )

    @http.route(
        ["/my/equipment/lists", "/my/equipment/lists/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_equipment_lists(self, page=1, list_kind=None, **kwargs):
        values = self._prepare_portal_layout_values()
        Config = request.env["adventure.equipment.configuration"]
        domain = self._get_list_domain(list_kind=list_kind)
        total = Config.search_count(domain)
        pager_values = portal_pager(
            url="/my/equipment/lists",
            url_args={"list_kind": list_kind} if list_kind else None,
            total=total,
            page=page,
            step=self._items_per_page,
        )
        lists = Config.search(
            domain,
            order="sequence, name, id desc",
            limit=self._items_per_page,
            offset=pager_values["offset"],
        )
        values.update(
            {
                "equipment_lists": lists,
                "page_name": "equipment_lists",
                "pager": pager_values,
                "default_url": "/my/equipment/lists",
                "list_kind_filter": list_kind,
            }
        )
        return request.render(
            "adventure_equipment_configuration_portal.portal_my_equipment_lists",
            values,
        )

    @http.route(
        ["/my/equipment/lists/new"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_my_equipment_list_new(self, **post):
        error = False
        if request.httprequest.method == "POST":
            name = (post.get("name") or "").strip()
            list_kind = post.get("list_kind")
            customer_note = (post.get("customer_note") or "").strip()
            if list_kind not in ("packing", "configuration"):
                error = _("Please choose Packing list or Configuration.")
            elif not name:
                error = _("Please provide a name.")
            else:
                try:
                    record = request.env["adventure.equipment.configuration"].create(
                        {
                            "name": name,
                            "list_kind": list_kind,
                            "partner_id": request.env.user.partner_id.id,
                            "company_id": request.env.company.id,
                            "customer_note": customer_note or False,
                        }
                    )
                    return request.redirect("/my/equipment/lists/%s" % record.id)
                except AccessError:
                    error = _("You are not allowed to create this list.")
                except Exception:
                    error = _("Could not create the list. Please try again.")

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "page_name": "equipment_lists",
                "error": error,
                "post": post,
            }
        )
        return request.render(
            "adventure_equipment_configuration_portal.portal_my_equipment_list_new",
            values,
        )

    @http.route(
        ["/my/equipment/lists/<int:list_id>"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_my_equipment_list_detail(self, list_id, **post):
        try:
            record = self._document_check_access(
                "adventure.equipment.configuration", list_id
            )
        except (AccessError, MissingError):
            return request.redirect("/my/equipment/lists")

        error = False
        if request.httprequest.method == "POST":
            action = post.get("action")
            try:
                if action == "reset_checks":
                    record.action_reset_checks()
                elif action == "delete_list":
                    record.unlink()
                    return request.redirect("/my/equipment/lists")
                elif action == "add_item":
                    # Unified checklist add: link equipment if chosen, else free-text item.
                    # Optional list-specific subtext (notes) applies to either kind.
                    asset_raw = (post.get("asset_id") or "").strip()
                    label = (post.get("label") or "").strip()
                    notes = (post.get("notes") or "").strip() or False
                    if asset_raw:
                        asset_id = int(asset_raw)
                        asset = request.env["adventure.equipment.asset"].browse(asset_id)
                        if (
                            not asset.exists()
                            or asset.partner_id != request.env.user.partner_id
                        ):
                            raise ValidationError(_("Invalid equipment selection."))
                        request.env["adventure.equipment.configuration.line"].create(
                            {
                                "configuration_id": record.id,
                                "line_type": "asset",
                                "asset_id": asset.id,
                                "notes": notes,
                            }
                        )
                    elif label:
                        request.env["adventure.equipment.configuration.line"].create(
                            {
                                "configuration_id": record.id,
                                "line_type": "text",
                                "name": label,
                                "notes": notes,
                            }
                        )
                    else:
                        raise ValidationError(_("Type an item or pick equipment to add."))
                elif action == "add_asset":
                    asset_id = int(post.get("asset_id") or 0)
                    asset = request.env["adventure.equipment.asset"].browse(asset_id)
                    if not asset.exists() or asset.partner_id != request.env.user.partner_id:
                        raise ValidationError(_("Invalid equipment selection."))
                    notes = (post.get("notes") or "").strip() or False
                    request.env["adventure.equipment.configuration.line"].create(
                        {
                            "configuration_id": record.id,
                            "line_type": "asset",
                            "asset_id": asset.id,
                            "notes": notes,
                        }
                    )
                elif action == "add_text":
                    label = (post.get("label") or "").strip()
                    notes = (post.get("notes") or "").strip()
                    request.env["adventure.equipment.configuration.line"].create(
                        {
                            "configuration_id": record.id,
                            "line_type": "text",
                            "name": label,
                            "notes": notes or False,
                        }
                    )
                elif action == "add_quantity":
                    label = (post.get("label") or "").strip() or False
                    notes = (post.get("notes") or "").strip() or False
                    quantity = post.get("quantity") or False
                    uom = (post.get("quantity_uom_label") or "").strip() or False
                    qty_val = float(quantity) if quantity not in (None, "", False) else 0.0
                    request.env["adventure.equipment.configuration.line"].create(
                        {
                            "configuration_id": record.id,
                            "line_type": "quantity",
                            "name": label,
                            "quantity": qty_val,
                            "quantity_uom_label": uom,
                            "notes": notes,
                        }
                    )
                elif action == "toggle_check":
                    line = self._document_check_access(
                        "adventure.equipment.configuration.line",
                        int(post.get("line_id") or 0),
                    )
                    line.action_toggle_checked()
                elif action == "move_up":
                    line = self._document_check_access(
                        "adventure.equipment.configuration.line",
                        int(post.get("line_id") or 0),
                    )
                    line.action_move_up()
                elif action == "move_down":
                    line = self._document_check_access(
                        "adventure.equipment.configuration.line",
                        int(post.get("line_id") or 0),
                    )
                    line.action_move_down()
                elif action == "delete_line":
                    line = self._document_check_access(
                        "adventure.equipment.configuration.line",
                        int(post.get("line_id") or 0),
                    )
                    line.unlink()
                elif action in ("edit_line", "edit_text_line"):
                    # Any list line may carry list-specific subtext (notes).
                    # Manual text/quantity rows can also rename; linked equipment keeps its asset label.
                    line = self._document_check_access(
                        "adventure.equipment.configuration.line",
                        int(post.get("line_id") or 0),
                    )
                    notes = (post.get("notes") or "").strip() or False
                    vals = {"notes": notes}
                    is_manual = not line.asset_id and line.line_type in ("text", "quantity")
                    if is_manual:
                        label = (post.get("label") or "").strip()
                        if not label:
                            raise ValidationError(_("Item text cannot be empty."))
                        vals["name"] = label
                        if line.line_type == "quantity":
                            quantity = post.get("quantity")
                            if quantity not in (None, "", False):
                                vals["quantity"] = float(quantity)
                            if "quantity_uom_label" in post:
                                uom = (post.get("quantity_uom_label") or "").strip()
                                vals["quantity_uom_label"] = uom or False
                        else:
                            vals["line_type"] = "text"
                    line.write(vals)
                return request.redirect("/my/equipment/lists/%s" % record.id)
            except AccessError:
                error = _("You are not allowed to change this list.")
            except (ValidationError, ValueError) as exc:
                error = str(exc)
            except Exception:
                error = _("Could not update the list. Please try again.")

        edit_line_id = False
        raw_edit = post.get("edit_line")
        if raw_edit not in (None, "", False):
            try:
                edit_line_id = int(raw_edit)
            except (TypeError, ValueError):
                edit_line_id = False

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "equipment_list": record,
                "page_name": "equipment_lists",
                "error": error,
                "edit_line_id": edit_line_id,
            }
        )
        return request.render(
            "adventure_equipment_configuration_portal.portal_my_equipment_list_detail",
            values,
        )

    @http.route(
        ["/my/equipment/lists/<int:list_id>/suggest"],
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
    )
    def portal_my_equipment_list_suggest(self, list_id, q="", **kwargs):
        """Autocomplete owned equipment for checklist add (loose wildcard)."""
        from .equipment_suggest import (
            asset_suggest_domain,
            format_suggest_results,
            rank_suggest_assets,
            tokenize_suggest_query,
        )

        try:
            record = self._document_check_access(
                "adventure.equipment.configuration", int(list_id)
            )
        except (AccessError, MissingError):
            return request.make_json_response({"results": []})

        query = (q or "").strip()
        if not tokenize_suggest_query(query):
            return request.make_json_response({"results": []})

        already = record.line_ids.mapped("asset_id").ids
        domain = asset_suggest_domain(
            request.env.user.partner_id.id,
            query,
            exclude_ids=already,
        )
        # Over-fetch then rank so category hits surface even if name order differs.
        assets = request.env["adventure.equipment.asset"].search(domain, limit=40)
        ranked = rank_suggest_assets(assets, query)[:12]
        return request.make_json_response(
            {"results": format_suggest_results(ranked, query)}
        )

    @http.route(
        ["/my/equipment/lists/<int:list_id>/edit"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_my_equipment_list_edit(self, list_id, **post):
        try:
            record = self._document_check_access(
                "adventure.equipment.configuration", list_id
            )
        except (AccessError, MissingError):
            return request.redirect("/my/equipment/lists")

        error = False
        if request.httprequest.method == "POST":
            vals = {
                "name": (post.get("name") or "").strip() or record.name,
                "customer_note": (post.get("customer_note") or "").strip() or False,
                "description": (post.get("description") or "").strip() or False,
            }
            if not record.line_ids:
                list_kind = post.get("list_kind")
                if list_kind in ("packing", "configuration"):
                    vals["list_kind"] = list_kind
            try:
                record.write(vals)
                return request.redirect("/my/equipment/lists/%s" % record.id)
            except AccessError:
                error = _("You are not allowed to update this list.")
            except ValidationError as exc:
                error = str(exc)
            except Exception:
                error = _("Could not save your changes. Please try again.")

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "equipment_list": record,
                "page_name": "equipment_lists",
                "error": error,
            }
        )
        return request.render(
            "adventure_equipment_configuration_portal.portal_my_equipment_list_edit",
            values,
        )
