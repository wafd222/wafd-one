"""Final verification after the 4.8.8 schema and reference-data migration."""

import frappe


SNACK_CATEGORY = "وجبة خفيفة / Snack"


def execute():
    """Verify the recipe category is available after DocType synchronization."""
    meta = frappe.get_meta("WAFD Recipe")
    field = meta.get_field("meal_category")
    options = [value.strip() for value in (field.options or "").splitlines() if value.strip()]
    if SNACK_CATEGORY not in options:
        frappe.throw(
            "WAFD Recipe.meal_category is missing the required option: " + SNACK_CATEGORY
        )
