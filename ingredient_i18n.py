"""Language-aware display labels for ingredients without changing Link values.

Ingredient names are document identifiers and are therefore kept stable.  The
helpers in this module return a translated label for presentation and search,
while forms and stock movements continue to submit the original name.
"""

from __future__ import annotations

import frappe


LANGUAGE_FIELDS = {
    "en": "ingredient_name_en",
    "bn": "ingredient_name_bn",
    "ur": "ingredient_name_ur",
    "hi": "ingredient_name_hi",
    "id": "ingredient_name_id",
    "fr": "ingredient_name_fr",
    "ha": "ingredient_name_ha",
    "sw": "ingredient_name_sw",
    "uz": "ingredient_name_uz",
}


def normalize_language(language=None):
    code = (language or "").strip().lower().replace("_", "-").split("-", 1)[0]
    return code if code == "ar" or code in LANGUAGE_FIELDS else "ar"


def language_field(language=None):
    return LANGUAGE_FIELDS.get(normalize_language(language))


def get_ingredient_labels(names, language=None):
    """Return {canonical name: translated display name} in one database query."""
    canonical = list(dict.fromkeys(name for name in names if name))
    if not canonical:
        return {}
    field = language_field(language)
    if not field:
        return {name: name for name in canonical}
    rows = frappe.get_all(
        "WAFD Ingredient",
        filters={"name": ["in", canonical]},
        fields=["name", field],
        limit_page_length=max(len(canonical), 1),
    )
    labels = {row.name: (row.get(field) or row.name) for row in rows}
    return {name: labels.get(name, name) for name in canonical}


def add_ingredient_labels(rows, language=None, key="ingredient"):
    labels = get_ingredient_labels((row.get(key) for row in rows), language)
    for row in rows:
        row["ingredient_label"] = labels.get(row.get(key), row.get(key))
    return rows
