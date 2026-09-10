"""Small, role-scoped data service for the mobile storekeeper home."""

import frappe
from frappe import _


ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}


def _check_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("غير مصرح لك بفتح شاشة أمين المستودع / Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_storekeeper_snapshot(warehouse=None, search=None):
    """Return a compact, read-only balance snapshot for the simplified page."""
    _check_access()

    warehouses = frappe.get_list(
        "WAFD Warehouse",
        filters={"status": "نشط / Active"},
        fields=["name", "warehouse_name", "warehouse_type"],
        order_by="warehouse_name asc",
        limit_page_length=100,
    )

    filters = {}
    if warehouse:
        filters["warehouse"] = warehouse
    or_filters = None
    cleaned_search = (search or "").strip()
    if cleaned_search:
        like = f"%{cleaned_search}%"
        or_filters = {"ingredient": ["like", like], "warehouse": ["like", like]}

    balance_args = {
        "filters": filters,
        "fields": [
            "name", "warehouse", "ingredient", "uom", "actual_quantity",
            "reserved_quantity", "available_quantity", "last_movement_date",
        ],
        "order_by": "warehouse asc, ingredient asc",
        "limit_page_length": 1000,
    }
    if or_filters:
        balance_args["or_filters"] = or_filters
    balances = frappe.get_list("WAFD Stock Balance", **balance_args)

    pending_orders = frappe.get_list(
        "WAFD Purchase Order",
        filters={"status": ["in", ["معتمد / Approved", "مرسل / Sent", "مستلم جزئياً / Partially Received"]]},
        fields=["name"],
        limit_page_length=500,
    )
    return {
        "warehouses": warehouses,
        "balances": balances,
        "pending_purchase_orders": len(pending_orders),
    }
