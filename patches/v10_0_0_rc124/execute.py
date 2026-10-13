from __future__ import annotations

import frappe


def execute():
    # User-approved Zamzam reference cost: 9 SAR. Preserve later/manual higher prices.
    ingredient = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": "ماء زمزم 330 مل"}, ["name", "standard_cost", "latest_market_cost"], as_dict=True)
    if ingredient:
        current = float(ingredient.latest_market_cost or ingredient.standard_cost or 0)
        if current <= 1.5:
            frappe.db.set_value("WAFD Ingredient", ingredient.name, {
                "standard_cost": 9.0,
                "latest_market_cost": 9.0,
                "latest_price_source": "اعتماد تشغيلي / Operational Reference",
                "cost_basis": "تقديري / Estimated",
            }, update_modified=False)

    # Print formats/pages are synced by Frappe migration. Clear only relevant caches.
    for dt in ("WAFD Iftar Project", "WAFD Iftar Daily Operation"):
        frappe.clear_cache(doctype=dt)
    frappe.clear_cache()
