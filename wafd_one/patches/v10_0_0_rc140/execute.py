from __future__ import annotations

import frappe
from frappe.utils import flt

PAID_ADDONS = {
    "معمول", "فواكه مجففة", "مكسرات مشكلة", "لوزين",
    "عصير برتقال 200 مل", "عصير تفاح 200 مل",
}
STANDARD_TEMPLATES = {
    "الوجبة القياسية / Standard Iftar",
    "وجبة مع زمزم / Iftar + Zamzam",
}

def execute():
    # Repair stale values produced by older RCs without touching custom packages.
    projects = frappe.get_all(
        "WAFD Iftar Project",
        filters={"meal_template": ["in", list(STANDARD_TEMPLATES)]},
        fields=["name"],
        limit_page_length=0,
    )
    for row in projects:
        addon_total = 0.0
        components = frappe.get_all(
            "WAFD Iftar Component",
            filters={"parent": row.name, "parenttype": "WAFD Iftar Project", "parentfield": "components"},
            fields=["ingredient", "cost_per_meal"],
            limit_page_length=0,
        )
        for component in components:
            ingredient_name = frappe.db.get_value("WAFD Ingredient", component.ingredient, "ingredient_name") or component.ingredient or ""
            if ingredient_name.strip() in PAID_ADDONS:
                addon_total += flt(component.cost_per_meal)
        frappe.db.set_value(
            "WAFD Iftar Project", row.name,
            {"sale_price_per_meal": flt(9.0 + addon_total, 2), "zamzam_reference_price": 1.50},
            update_modified=False,
        )
