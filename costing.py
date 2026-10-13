"""Costing and profitability utilities for WAFD ONE."""
from __future__ import annotations

import frappe
from frappe.utils import cint, flt, now_datetime, nowdate


def get_costing_settings() -> dict[str, float]:
    defaults = {
        "default_waste_percent": 3.0,
        "default_overhead_percent": 10.0,
        "default_target_margin_percent": 20.0,
        "default_vat_rate": 15.0,
        "budget_warning_percent": 90.0,
        "budget_exceeded_percent": 100.0,
    }
    if frappe.db.exists("DocType", "WAFD Costing Settings"):
        try:
            doc = frappe.get_single("WAFD Costing Settings")
            for key in defaults:
                if doc.get(key) is not None:
                    defaults[key] = flt(doc.get(key))
        except Exception:
            frappe.log_error(frappe.get_traceback(), "WAFD Costing Settings Read")
    return defaults


def resolve_ingredient_cost(ingredient_name: str) -> float:
    row = frappe.db.get_value(
        "WAFD Ingredient",
        ingredient_name,
        ["latest_market_cost", "standard_cost"],
        as_dict=True,
    ) or {}
    return flt(row.get("latest_market_cost")) or flt(row.get("standard_cost"))


def refresh_ingredient_cost_from_stock(ingredient: str) -> dict:
    """Refresh ingredient cost from weighted stock and recalculate affected recipes.

    This function is retained for compatibility with the stock-movement workflow.
    """
    balances = frappe.get_all(
        "WAFD Stock Balance",
        filters={"ingredient": ingredient, "actual_quantity": [">", 0]},
        fields=["actual_quantity", "average_cost"],
    )
    quantity = sum(flt(row.actual_quantity) for row in balances)
    value = sum(flt(row.actual_quantity) * flt(row.average_cost) for row in balances)
    if quantity <= 0:
        return {"ingredient": ingredient, "updated": False}

    weighted_cost = value / quantity
    frappe.db.set_value(
        "WAFD Ingredient",
        ingredient,
        {
            "standard_cost": weighted_cost,
            "latest_market_cost": weighted_cost,
            "latest_price_date": nowdate(),
            "latest_price_source": "متوسط المخزون الفعلي / Weighted Inventory Average",
            "cost_basis": "آخر فاتورة مورد / Latest Supplier Invoice",
            "cost_last_updated": now_datetime(),
            "cost_confidence": "عالية / High",
        },
        update_modified=True,
    )

    recipes = frappe.get_all(
        "WAFD Recipe Item", filters={"ingredient": ingredient}, pluck="parent"
    )
    refreshed = 0
    for recipe_name in sorted(set(recipes)):
        if not frappe.db.exists("WAFD Recipe", recipe_name):
            continue
        recalculate_recipe_cost(recipe_name, save=True, ignore_permissions=True)
        refreshed += 1

    return {
        "ingredient": ingredient,
        "updated": True,
        "standard_cost": weighted_cost,
        "recipes_refreshed": refreshed,
    }


def refresh_costs_after_stock_movement(doc) -> list[dict]:
    """Refresh costs after receipt or adjustment stock movements."""
    if doc.movement_type not in ("استلام / Receipt", "تسوية / Adjustment"):
        return []
    ingredients = sorted({row.ingredient for row in doc.items or [] if row.ingredient})
    return [refresh_ingredient_cost_from_stock(name) for name in ingredients]


@frappe.whitelist()
def recalculate_recipe_cost(recipe_name: str, save=True, ignore_permissions=False) -> dict:
    doc = frappe.get_doc("WAFD Recipe", recipe_name)
    if not cint(ignore_permissions):
        doc.check_permission("write")

    settings = get_costing_settings()
    yield_qty = flt(doc.yield_quantity)
    if yield_qty <= 0:
        frappe.throw("عدد الحصص يجب أن يكون أكبر من صفر / Yield must be greater than zero")

    direct_total = 0.0
    for row in doc.items or []:
        row.unit_cost = resolve_ingredient_cost(row.ingredient)
        row.amount = flt(row.quantity) * flt(row.unit_cost)
        direct_total += flt(row.amount)

    waste_percent = flt(doc.waste_percent)
    overhead_percent = flt(doc.overhead_percent)
    margin_percent = flt(doc.profit_margin_percent)
    if waste_percent < 0 or overhead_percent < 0:
        frappe.throw("نسب الهدر والمصاريف لا يمكن أن تكون سالبة / Cost percentages cannot be negative")
    if margin_percent < 0 or margin_percent >= 100:
        frappe.throw("هامش الربح يجب أن يكون بين 0 وأقل من 100% / Margin must be below 100%")

    direct_per_portion = direct_total / yield_qty
    waste_cost = direct_per_portion * waste_percent / 100
    subtotal = (
        direct_per_portion
        + waste_cost
        + flt(doc.packaging_cost_per_portion)
        + flt(doc.labor_cost_per_portion)
        + flt(doc.utilities_cost_per_portion)
        + flt(doc.delivery_cost_per_portion)
    )
    full_cost = subtotal * (1 + overhead_percent / 100)
    price_ex_vat = full_cost / (1 - margin_percent / 100)

    doc.direct_ingredient_cost = direct_total
    doc.total_cost = direct_total
    doc.cost_per_portion = direct_per_portion
    doc.full_cost_per_portion = full_cost
    doc.recommended_price_ex_vat = price_ex_vat
    doc.recommended_price_incl_vat = price_ex_vat * (
        1 + settings["default_vat_rate"] / 100
    )
    doc.costed_on = now_datetime()

    if cint(save):
        doc.save(ignore_permissions=cint(ignore_permissions))

    return {
        "recipe": doc.name,
        "direct_total": direct_total,
        "full_cost_per_portion": full_cost,
        "recommended_price_ex_vat": price_ex_vat,
        "recommended_price_incl_vat": doc.recommended_price_incl_vat,
    }


@frappe.whitelist()
def create_project_cost_snapshot(project_name: str) -> str:
    from wafd_one.finance import refresh_project_financials

    values = refresh_project_financials(project_name) or {}
    project = frappe.db.get_value(
        "WAFD Catering Project",
        project_name,
        ["estimated_cost", "contract_value", "total_meals"],
        as_dict=True,
    ) or {}
    estimated = flt(project.get("estimated_cost"))
    actual = flt(values.get("actual_cost"))
    variance = actual - estimated
    variance_percent = variance / estimated * 100 if estimated else 0

    snapshot_values = {
        "estimated_cost": estimated,
        "actual_cost": actual,
        "cost_variance": variance,
        "cost_variance_percent": variance_percent,
        "revenue": flt(values.get("revenue")),
        "profit": flt(values.get("profit")),
        "profit_margin_percent": flt(values.get("profit_margin_percent")),
        "cost_per_meal": flt(values.get("cost_per_meal")),
        "profit_per_meal": flt(values.get("profit_per_meal")),
        "delivered_meals": flt(values.get("delivered_meals")),
    }

    existing = frappe.db.get_value(
        "WAFD Cost Snapshot",
        {"project": project_name, "snapshot_date": nowdate()},
        "name",
    )
    if existing:
        frappe.db.set_value(
            "WAFD Cost Snapshot", existing, snapshot_values, update_modified=False
        )
        return existing

    doc = frappe.get_doc(
        {
            "doctype": "WAFD Cost Snapshot",
            "project": project_name,
            "snapshot_date": nowdate(),
            **snapshot_values,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def daily_costing_refresh() -> None:
    projects = frappe.get_all(
        "WAFD Catering Project",
        filters={"status": ["!=", "ملغي / Cancelled"]},
        pluck="name",
    )
    for project in projects:
        try:
            create_project_cost_snapshot(project)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"WAFD Cost Snapshot {project}")
