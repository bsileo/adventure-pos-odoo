# -*- coding: utf-8 -*-

from odoo import api, models

from odoo.addons.adventure_product_category.utils.vendor_category_matcher import (
    match_vendor_category,
)


class AdventureVendorCategoryMatchService(models.AbstractModel):
    """Service API: fuzzy-map vendor category strings to ``product.category`` records."""

    _name = "adventure.vendor_category_match"
    _description = "Vendor category fuzzy matching service"

    @api.model
    def match_vendor_category(
        self,
        vendor_text,
        threshold=80.0,
        top_n=5,
        category_domain=None,
    ):
        """
        Match a vendor category string to the best ``product.category`` by name,
        canonical_name, alias_names, and keywords (RapidFuzz WRatio).

        :param str vendor_text: Vendor-supplied category label.
        :param float threshold: If best score is below this (0–100), ``needs_review`` is True.
        :param int top_n: Number of top candidates returned for auditing.
        :param list | None category_domain: Optional Odoo domain passed to ``search``.
        :return: dict with category_id, confidence, needs_review, candidates
        """
        Category = self.env["product.category"]
        domain = category_domain if category_domain is not None else []
        records = Category.search(domain)

        rows = []
        for c in records:
            aliases = c.alias_names
            if not isinstance(aliases, list):
                aliases = []
            kws = c.keywords
            if not isinstance(kws, list):
                kws = []
            rows.append(
                {
                    "id": c.id,
                    "name": c.name or "",
                    "canonical_name": c.canonical_name or "",
                    "alias_names": [a for a in aliases if isinstance(a, str)],
                    "keywords": [k for k in kws if isinstance(k, str)],
                }
            )

        return match_vendor_category(
            vendor_text or "",
            rows,
            threshold=float(threshold),
            top_n=int(top_n),
        )
