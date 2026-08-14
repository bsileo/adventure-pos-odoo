# -*- coding: utf-8 -*-
"""Owned-equipment autocomplete helpers for packing list checklist add."""

from odoo.fields import Domain

# Fields searched with ilike for each query token (OR within a token).
_SUGGEST_CHAR_FIELDS = (
    "nickname",
    "name",
    "display_name",
    "brand_name",
    "model_name",
    "manufacturer_name",
    "serial_number",
    "customer_note",
    "description",
    "snapshot_category",
    "snapshot_product_name",
    "snapshot_brand",
    "snapshot_model",
)

_SUGGEST_RELATED_FIELDS = (
    "category_id.name",
    "category_id.code",
    "tag_ids.name",
)


def tokenize_suggest_query(query):
    """Split a user query into lowercase tokens for AND matching."""
    return [token for token in (query or "").strip().lower().split() if token]


def asset_suggest_domain(partner_id, query, exclude_ids=None):
    """
    Domain for loose owned-equipment autocomplete.

    Each token must match at least one searchable field (AND across tokens,
    OR across fields). Empty/whitespace query yields an empty-result domain.
    """
    tokens = tokenize_suggest_query(query)
    if not tokens:
        return Domain("id", "=", False)

    domain = Domain("partner_id", "=", partner_id) & Domain("active", "=", True)
    if exclude_ids:
        domain &= Domain("id", "not in", list(exclude_ids))

    searchable = _SUGGEST_CHAR_FIELDS + _SUGGEST_RELATED_FIELDS
    for token in tokens:
        domain &= Domain.OR(
            [Domain(field, "ilike", token) for field in searchable]
        )
    return domain


def _haystacks(asset):
    """Lowercase strings used for ranking / match hints."""
    category_name = asset.category_id.name or ""
    category_code = asset.category_id.code or ""
    return {
        "category": category_name.lower(),
        "category_code": category_code.lower(),
        "nickname": (asset.nickname or "").lower(),
        "model": (asset.model_name or "").lower(),
        "brand": (asset.brand_name or "").lower(),
        "manufacturer": (asset.manufacturer_name or "").lower(),
        "display": (asset.display_name or "").lower(),
        "serial": (asset.serial_number or "").lower(),
        "note": (asset.customer_note or "").lower(),
        "snapshot_category": (asset.snapshot_category or "").lower(),
        "tags": " ".join(asset.tag_ids.mapped("name")).lower(),
    }


def match_hint_for_asset(asset, tokens):
    """Short explanation of why this asset matched (for suggestion meta)."""
    if not tokens:
        return asset.category_id.display_name or ""
    bags = _haystacks(asset)
    for token in tokens:
        if token in bags["category"] or token in bags["category_code"]:
            return "Category: %s" % (
                asset.category_id.display_name or asset.category_id.name
            )
        if token in bags["snapshot_category"]:
            return "Category: %s" % asset.snapshot_category
        if token in bags["tags"]:
            return "Tag match"
        if token in bags["nickname"]:
            return asset.category_id.display_name or "Nickname match"
        if (
            token in bags["brand"]
            or token in bags["model"]
            or token in bags["manufacturer"]
        ):
            return asset.category_id.display_name or "Brand / model match"
    return asset.category_id.display_name or ""


def rank_suggest_assets(assets, query):
    """
    Rank matches: category hits first, then nickname/brand/model, then others.
    Stable secondary sort by nickname/display_name.
    """
    tokens = tokenize_suggest_query(query)
    scored = []
    for asset in assets:
        bags = _haystacks(asset)
        score = 0
        for token in tokens:
            if token in bags["category"] or token in bags["category_code"]:
                score += 100
            if token in bags["snapshot_category"]:
                score += 90
            if token in bags["nickname"]:
                score += 50
            if (
                token in bags["brand"]
                or token in bags["model"]
                or token in bags["manufacturer"]
            ):
                score += 40
            if token in bags["tags"]:
                score += 30
            if (
                token in bags["display"]
                or token in bags["serial"]
                or token in bags["note"]
            ):
                score += 10
        label = (asset.nickname or asset.display_name or "").lower()
        scored.append((-score, label, asset.id, asset))
    scored.sort()
    return [row[3] for row in scored]


def format_suggest_results(assets, query):
    """JSON-serializable suggestion rows."""
    tokens = tokenize_suggest_query(query)
    return [
        {
            "id": asset.id,
            "label": asset.display_name,
            "category": asset.category_id.display_name or "",
            "match_hint": match_hint_for_asset(asset, tokens),
        }
        for asset in assets
    ]
