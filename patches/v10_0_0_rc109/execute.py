import frappe
from frappe.utils import flt, now_datetime

REFERENCE_COSTS = {
    "ملعقة": 0.04,
    "خبز فتوت": 0.45,
    "غلاف إفطار صائم": 0.12,
    "غلاف شركة وفد المدينة": 0.10,
    "منديل معطر": 0.08,
}

def execute():
    for ingredient_name, cost in REFERENCE_COSTS.items():
        name = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": ingredient_name}, "name")
        if not name:
            continue
        current = frappe.db.get_value("WAFD Ingredient", name, ["latest_market_cost", "standard_cost"], as_dict=True) or {}
        if flt(current.get("latest_market_cost")) or flt(current.get("standard_cost")):
            continue
        frappe.db.set_value("WAFD Ingredient", name, {
            "standard_cost": cost,
            "cost_basis": "سعر مرجعي تشغيلي قابل للتحديث / Editable Operational Reference",
            "cost_last_updated": now_datetime(),
        }, update_modified=False)
    frappe.clear_cache(doctype="WAFD Iftar Project")
