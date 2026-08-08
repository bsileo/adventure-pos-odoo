# -*- coding: utf-8 -*-

import re

from odoo import api, models

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)


class AdventureProductSearch(models.AbstractModel):
    """Deterministic product search used by AI tools and non-AI callers."""

    _name = "adventure.product_search"
    _description = "Adventure product search service"

    @api.model
    def search_products(
        self,
        query,
        limit=20,
        available_in_pos_only=True,
        category_name=None,
    ):
        query = (query or "").strip()
        limit = max(1, min(int(limit or 20), 50))
        if not query:
            return {"query": query, "products": [], "count": 0}

        tokens = self._tokenize(query)
        Product = self.env["product.product"]
        domain = [("sale_ok", "=", True), ("active", "=", True)]
        if available_in_pos_only and "available_in_pos" in Product._fields:
            domain.append(("available_in_pos", "=", True))
        elif available_in_pos_only and "available_in_pos" in self.env["product.template"]._fields:
            domain.append(("product_tmpl_id.available_in_pos", "=", True))
        if category_name:
            domain.append(("categ_id.name", "ilike", category_name))

        leafs = []
        for token in tokens[:8]:
            leafs.append(("name", "ilike", token))
            leafs.append(("default_code", "ilike", token))
            if "barcode" in Product._fields:
                leafs.append(("barcode", "ilike", token))
            leafs.append(("product_tmpl_id.name", "ilike", token))
        if leafs:
            or_expr = ["|"] * (len(leafs) - 1) + leafs
            domain = domain + or_expr
        else:
            domain = domain + [("name", "ilike", query)]

        candidates = Product.search(domain, limit=max(limit * 5, 50))
        scored = []
        query_lower = query.lower()
        for product in candidates:
            score = self._score_product(product, tokens, query_lower)
            if score <= 0:
                continue
            tmpl = product.product_tmpl_id
            scored.append(
                {
                    "product_id": product.id,
                    "product_tmpl_id": tmpl.id,
                    "name": product.display_name,
                    "default_code": product.default_code or "",
                    "barcode": product.barcode or "",
                    "list_price": float(product.lst_price or getattr(product, "list_price", 0.0) or 0.0),
                    "categ_id": product.categ_id.id if product.categ_id else False,
                    "categ_name": product.categ_id.display_name if product.categ_id else "",
                    "available_in_pos": bool(
                        getattr(product, "available_in_pos", False)
                        or getattr(tmpl, "available_in_pos", False)
                    ),
                    "score": score,
                }
            )

        scored.sort(key=lambda row: (-row["score"], row["name"]))
        products = scored[:limit]
        return {
            "query": query,
            "tokens": tokens,
            "products": products,
            "count": len(products),
        }

    def _tokenize(self, query):
        tokens = [t.lower() for t in TOKEN_RE.findall(query or "") if len(t) > 1]
        stop = {"the", "and", "for", "with", "size", "a", "an", "of", "to"}
        return [t for t in tokens if t not in stop] or [query.lower()]

    def _score_product(self, product, tokens, query_lower):
        name = (product.display_name or "").lower()
        code = (product.default_code or "").lower()
        barcode = (product.barcode or "").lower()
        categ = (product.categ_id.display_name or "").lower()
        haystack = " ".join([name, code, barcode, categ])
        score = 0
        if query_lower and query_lower in name:
            score += 80
        if code and code == query_lower:
            score += 100
        if barcode and barcode == query_lower:
            score += 100
        for token in tokens:
            if token in name:
                score += 20
            if token and code and token in code:
                score += 25
            if token and barcode and token in barcode:
                score += 25
            if token in categ:
                score += 8
            if len(token) >= 3 and token in haystack:
                score += 3
        return score
