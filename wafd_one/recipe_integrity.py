"""Shared recipe integrity guards used before production is generated."""
from __future__ import annotations

import frappe
from frappe.utils import flt

ACTIVE = "نشطة / Active"


def validate_recipe_ready(recipe_name: str | None, row_index: int | None = None) -> None:
    """Reject missing/inactive/empty recipes with the exact recipe name."""
    if not recipe_name:
        return
    values = frappe.db.get_value("WAFD Recipe", recipe_name, ["recipe_name", "status"], as_dict=True)
    label = recipe_name
    suffix = f" (الصف {row_index} / row {row_index})" if row_index else ""
    if not values:
        frappe.throw(f"الوصفة «{label}» غير موجودة{suffix} / Recipe “{label}” does not exist{suffix}")
    if values.status != ACTIVE:
        frappe.throw(
            f"الوصفة «{label}» غير نشطة أو غير جاهزة للتشغيل{suffix}. اختر وصفة مكتملة / "
            f"Recipe “{label}” is inactive or not production-ready{suffix}. Select a complete recipe."
        )
    rows = frappe.get_all(
        "WAFD Recipe Item",
        filters={"parent": recipe_name, "parenttype": "WAFD Recipe", "parentfield": "items"},
        fields=["ingredient", "quantity"],
        limit_page_length=0,
    )
    valid = [row for row in rows if row.ingredient and flt(row.quantity) > 0]
    if not valid:
        frappe.throw(
            f"الوصفة «{label}» لا تحتوي على مكونات تشغيلية{suffix}. "
            "أكمل مكوناتها أو اختر وصفة مكتملة قبل إنشاء الخطة / "
            f"Recipe “{label}” has no operational ingredients{suffix}. Complete its ingredients or select a production-ready recipe."
        )
