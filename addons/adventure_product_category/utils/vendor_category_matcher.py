# -*- coding: utf-8 -*-
"""Fuzzy match a vendor category string to internal category rows (no Odoo imports)."""

from __future__ import annotations

from typing import Any, TypedDict

from rapidfuzz import fuzz


class CategoryRow(TypedDict, total=False):
    """Minimal shape expected from Odoo or any other source."""

    id: int
    name: str
    canonical_name: str
    alias_names: list[str]
    keywords: list[str]


class MatchResult(TypedDict):
    category_id: int | None
    confidence: float
    needs_review: bool
    candidates: list[dict[str, Any]]


def _strings_for_category(row: CategoryRow) -> list[str]:
    out: list[str] = []
    for key in ("name", "canonical_name"):
        val = row.get(key)
        if val and isinstance(val, str) and val.strip():
            out.append(val.strip())
    for key in ("alias_names", "keywords"):
        seq = row.get(key) or []
        if not isinstance(seq, list):
            continue
        for item in seq:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
    return out


def _best_score_for_category(vendor_norm: str, row: CategoryRow) -> float:
    candidates = _strings_for_category(row)
    if not candidates:
        return 0.0
    return float(max(fuzz.WRatio(vendor_norm, c) for c in candidates))


def match_vendor_category(
    vendor_text: str,
    categories: list[CategoryRow],
    *,
    threshold: float = 80.0,
    top_n: int = 5,
) -> MatchResult:
    """
    Pick the product.category id with highest fuzzy score against name, canonical_name,
    alias_names, and keywords.

    :param vendor_text: Raw vendor-supplied category label.
    :param categories: Rows with at least ``id`` and optional match fields.
    :param threshold: Minimum confidence (0–100, same scale as WRatio) to avoid manual review.
    :param top_n: How many runner-up candidates to include for auditing or UI.
    """
    vendor_norm = (vendor_text or "").strip()
    if not vendor_norm or not categories:
        return {
            "category_id": None,
            "confidence": 0.0,
            "needs_review": True,
            "candidates": [],
        }

    scored: list[tuple[int, float]] = []
    for row in categories:
        cid = row.get("id")
        if cid is None:
            continue
        score = _best_score_for_category(vendor_norm, row)
        scored.append((int(cid), score))

    scored.sort(key=lambda x: (-x[1], x[0]))
    best_id, best_score = scored[0] if scored else (None, 0.0)

    if best_score <= 0.0:
        best_id = None

    candidates = [
        {"category_id": cid, "confidence": round(conf, 2)} for cid, conf in scored[:top_n]
    ]

    needs_review = best_id is None or best_score < threshold

    return {
        "category_id": best_id,
        "confidence": round(float(best_score), 2),
        "needs_review": bool(needs_review),
        "candidates": candidates,
    }
