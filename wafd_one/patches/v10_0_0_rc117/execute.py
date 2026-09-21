"""Seed/update Iftar ingredient reference costs safely.

This patch may be retried after a failed migration, so it must be idempotent.
"""

import frappe
from frappe.utils import flt

COST_BASIS = "تقديري / Estimated"
PRICE_SOURCE = "سعر مرجعي قابل للتعديل 2026 / Editable 2026 reference"
UOM = "حبة / Piece"

PRICES = {
    "زبادي": 1.15,
    "تمر": 0.25,
    "ماء 330 مل": 0.62,
    "ماء زمزم 330 مل": 1.50,
    "دقة مدينية": 0.04,
    "ملعقة": 0.04,
    "منديل معطر": 0.12,
    "خبز فتوت": 0.45,
    "غلاف إفطار صائم": 0.12,
    "غلاف شركة وفد المدينة": 0.10,
    "معمول": 0.75,
    "فواكه مجففة": 1.20,
    "مكسرات مشكلة": 1.50,
    "لوزين": 0.60,
    "عصير برتقال 200 مل": 1.20,
    "عصير تفاح 200 مل": 1.60,
}


def execute():
    for ingredient, price in PRICES.items():
        name = frappe.db.get_value(
            "WAFD Ingredient", {"ingredient_name": ingredient}, "name"
        )
        values = {
            "standard_cost": flt(price),
            "latest_market_cost": flt(price),
            "latest_price_source": PRICE_SOURCE,
            "cost_basis": COST_BASIS,
        }

        if name:
            # Direct DB update keeps the patch idempotent and avoids read-only
            # validation on latest_market_cost during migration retries.
            frappe.db.set_value(
                "WAFD Ingredient", name, values, update_modified=False
            )
            continue

        frappe.get_doc(
            {
                "doctype": "WAFD Ingredient",
                "ingredient_name": ingredient,
                "uom": UOM,
                **values,
            }
        ).insert(ignore_permissions=True)
