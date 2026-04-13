# -*- coding: utf-8 -*-
"""Fuzzy match a vendor category string to internal category rows (no Odoo imports)."""

from __future__ import annotations

import re
from typing import Any, TypedDict

from rapidfuzz import fuzz

# Delimiters that indicate a compound vendor category (e.g. "Regs/Octos", "Wetsuits & Drysuits")
_COMPOUND_SPLIT = re.compile(r"[/\\|,&]|\s+(?:and|or|with)\s+", re.IGNORECASE)


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


def _split_vendor_tokens(text: str) -> list[str]:
    """Split a compound vendor label into individual tokens.

    "Regs/Octos" → ["Regs", "Octos"]
    "Wetsuits & Drysuits" → ["Wetsuits", "Drysuits"]
    """
    parts = _COMPOUND_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]


def _best_score_for_category(vendor_norm: str, row: CategoryRow) -> float:
    cat_strings = _strings_for_category(row)
    if not cat_strings:
        return 0.0

    # Score the full vendor string as-is
    full_score = max(fuzz.WRatio(vendor_norm, c) for c in cat_strings)

    # For compound labels (e.g. "Regs/Octos"), also score each token independently.
    # This lets "Regs" match "Regulators" even when the full string scores poorly.
    tokens = _split_vendor_tokens(vendor_norm)
    if len(tokens) > 1:
        token_best = max(
            max(fuzz.WRatio(token, c) for c in cat_strings)
            for token in tokens
        )
        return float(max(full_score, token_best))

    return float(full_score)


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
