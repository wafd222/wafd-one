"""Install the curated RC295 material catalogue without touching stock history."""

from __future__ import annotations

import frappe

from wafd_one.material_catalog_rc295 import CATALOGUE
from wafd_one.master_data import preferred_warehouse_for_ingredient


def _available_code(wanted: str, ingredient_name: str) -> str:
    owner = frappe.db.get_value("WAFD Ingredient", {"item_code": wanted}, "name")
    if not owner or owner == ingredient_name:
        return wanted
    suffix = 2
    while frappe.db.exists("WAFD Ingredient", {"item_code": f"{wanted}-{suffix}"}):
        suffix += 1
    return f"{wanted}-{suffix}"


def execute():
    if not frappe.db.exists("DocType", "WAFD Ingredient"):
        return

    # Load the expanded Select options before applying the corrected categories.
    frappe.reload_doc("wafd_one", "doctype", "wafd_ingredient", force=True)

    for row in CATALOGUE:
        name = row["ingredient_name"]
        existing = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": name}, "name")
        values = {
            "category": row["category"],
            "uom": row["uom"],
            "preferred_warehouse": row["preferred_warehouse"] if frappe.db.exists(
                "WAFD Warehouse", row["preferred_warehouse"]
            ) else None,
            "storage_condition": row["storage_condition"],
            "status": "نشط / Active",
        }
        if existing:
            # Keep document names, item codes, prices, suppliers, reorder points,
            # stock balances and every posted movement intact.
            frappe.db.set_value("WAFD Ingredient", existing, values, update_modified=False)
            continue

        frappe.get_doc({
            "doctype": "WAFD Ingredient",
            "ingredient_name": name,
            "item_code": _available_code(row["item_code"], name),
            **values,
            "standard_cost": 0,
            "minimum_stock": 0,
            "verification_status": "تشغيلي داخلي / Internal Operational",
            "source_notes": "كتالوج مواد الإعاشة والمستودعات المنظم في الإصدار RC295؛ السعر والحد الأدنى يحددان من الإدارة.",
        }).insert(ignore_permissions=True)

    # Any non-catalogue legacy material keeps its name/category, but its storage
    # preference is refreshed from the corrected operational routing rules.
    for legacy in frappe.get_all("WAFD Ingredient", fields=["name", "ingredient_name", "category"]):
        preferred = preferred_warehouse_for_ingredient(legacy.ingredient_name or legacy.name, legacy.category)
        if preferred and frappe.db.exists("WAFD Warehouse", preferred):
            frappe.db.set_value(
                "WAFD Ingredient", legacy.name, "preferred_warehouse", preferred, update_modified=False
            )

    frappe.clear_cache(doctype="WAFD Ingredient")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()

