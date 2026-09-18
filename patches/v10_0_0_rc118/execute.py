"""Normalize ingredient pricing metadata after RC117 migration retries."""

import frappe

VALID_COST_BASIS = {
    "متوسط أسعار موثقة / Verified Price Average",
    "آخر فاتورة مورد / Latest Supplier Invoice",
    "تكلفة يدوية / Manual Cost",
    "تقديري / Estimated",
}
DEFAULT_COST_BASIS = "تقديري / Estimated"


def execute():
    invalid_rows = frappe.get_all(
        "WAFD Ingredient", fields=["name", "cost_basis"]
    )
    for row in invalid_rows:
        if row.cost_basis not in VALID_COST_BASIS:
            frappe.db.set_value(
                "WAFD Ingredient",
                row.name,
                "cost_basis",
                DEFAULT_COST_BASIS,
                update_modified=False,
            )
