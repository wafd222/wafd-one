"""Inventory-driven costing utilities for WAFD ONE v6.2.0."""
from __future__ import annotations
import frappe
from frappe.utils import flt, now_datetime


def refresh_ingredient_cost_from_stock(ingredient: str) -> dict:
    """Set ingredient standard cost from weighted on-hand stock and refresh affected recipes."""
    balances = frappe.get_all(
        "WAFD Stock Balance",
        filters={"ingredient": ingredient, "actual_quantity": [">", 0]},
        fields=["actual_quantity", "average_cost"],
    )
    qty = sum(flt(r.actual_quantity) for r in balances)
    value = sum(flt(r.actual_quantity) * flt(r.average_cost) for r in balances)
    if qty <= 0:
        return {"ingredient": ingredient, "updated": False}
    weighted = value / qty
    frappe.db.set_value("WAFD Ingredient", ingredient, {
        "standard_cost": weighted,
        "latest_market_cost": weighted,
        "latest_price_date": frappe.utils.nowdate(),
        "latest_price_source": "متوسط المخزون الفعلي / Weighted Inventory Average",
        "cost_basis": "آخر فاتورة مورد / Latest Supplier Invoice",
        "cost_last_updated": now_datetime(),
        "cost_confidence": "عالية / High",
    }, update_modified=True)
    recipes = frappe.get_all("WAFD Recipe Item", filters={"ingredient": ingredient}, pluck="parent")
    refreshed = 0
    for name in sorted(set(recipes)):
        if not frappe.db.exists("WAFD Recipe", name):
            continue
        doc = frappe.get_doc("WAFD Recipe", name)
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
        refreshed += 1
    return {"ingredient": ingredient, "updated": True, "standard_cost": weighted, "recipes_refreshed": refreshed}


def refresh_costs_after_stock_movement(doc) -> list[dict]:
    if doc.movement_type not in ("استلام / Receipt", "تسوية / Adjustment"):
        return []
    return [refresh_ingredient_cost_from_stock(x) for x in sorted({r.ingredient for r in doc.items or [] if r.ingredient})]
