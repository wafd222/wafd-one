"""Canonical unit-of-measure helpers for WAFD ONE.

Ingredient master values are bilingual (for example ``كجم / Kg``), while
legacy/imported rows may contain only Arabic or English labels.  Business
logic must compare semantic units, not translated display strings.
"""
from __future__ import annotations

import re


_CANONICAL_ALIASES = {
    "كجم / Kg": {"kg", "kgs", "kilogram", "kilograms", "كجم", "كيلو", "كيلوجرام"},
    "جرام / Gram": {"g", "gm", "gram", "grams", "جرام", "غرام"},
    "لتر / Liter": {"l", "lt", "ltr", "liter", "litre", "liters", "litres", "لتر"},
    "مل / ML": {"ml", "milliliter", "millilitre", "milliliters", "millilitres", "مل", "ملليلتر"},
    "حبة / Piece": {"piece", "pieces", "pc", "pcs", "unit", "units", "حبة", "حبه"},
    "كرتون / Carton": {"carton", "cartons", "ctn", "كرتون"},
    "صندوق / Box": {"box", "boxes", "صندوق"},
}


def _token(value: object) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"[\s_\-]+", " ", text)
    return text.strip()


def canonical_uom(value: object) -> str:
    """Return the bilingual canonical UOM when *value* is a known alias."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    token = _token(raw)
    for canonical, aliases in _CANONICAL_ALIASES.items():
        if token == _token(canonical):
            return canonical
        # Bilingual values may arrive in either half, e.g. ``Kg``.
        parts = {_token(part) for part in canonical.split("/")}
        if token in parts or token in {_token(alias) for alias in aliases}:
            return canonical
    return raw


def uom_matches(left: object, right: object) -> bool:
    if not left or not right:
        return True
    return canonical_uom(left) == canonical_uom(right)
