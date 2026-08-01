"""Create auditable acceptance-test opening stock for zero-balance ingredients.

This patch is intentionally idempotent:
- existing positive stock is never changed;
- only ingredients whose preferred warehouse balance is zero are initialized;
- one posted adjustment movement is recorded per warehouse for traceability.

The seeded quantities are based on each ingredient's configured minimum stock.
They are acceptance-test balances and must be reconciled with a physical count
before production use.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe.utils import flt, now_datetime

from wafd_one.master_data import CATEGORY_WAREHOUSE_MAP, INGREDIENTS, WAREHOUSES
from wafd_one.uom import canonical_uom

REFERENCE_MARKER = "RC50-ACCEPTANCE-OPENING-STOCK"
NOTE = (
    "RC50-ACCEPTANCE-OPENING-STOCK | "
    "رصيد افتتاحي اختباري للاعتماد النهائي؛ يجب مطابقته مع الجرد الفعلي قبل التشغيل. / "
    "Acceptance-test opening stock; reconcile with physical count before production."
)


def _ready() -> bool:
    required = (
        "WAFD Ingredient",
        "WAFD Warehouse",
        "WAFD Stock Balance",
        "WAFD Stock Movement",
        "WAFD Stock Movement Item",
    )
    return all(frappe.db.exists("DocType", doctype) for doctype in required)


def _preferred_warehouse(category: str) -> str | None:
    preferred = CATEGORY_WAREHOUSE_MAP.get(category)
    if preferred and frappe.db.exists("WAFD Warehouse", preferred):
        return preferred
    for warehouse_name, _warehouse_type, _location in WAREHOUSES:
        if frappe.db.exists("WAFD Warehouse", warehouse_name):
            return warehouse_name
    return None


def _balance(warehouse: str, ingredient: str):
    name = frappe.db.get_value(
        "WAFD Stock Balance",
        {"warehouse": warehouse, "ingredient": ingredient},
        "name",
    )
    return frappe.get_doc("WAFD Stock Balance", name) if name else None


def _ensure_balance(warehouse: str, ingredient: str, uom: str, cost: float):
    balance = _balance(warehouse, ingredient)
    if balance:
        return balance
    balance = frappe.get_doc(
        {
            "doctype": "WAFD Stock Balance",
            "warehouse": warehouse,
            "ingredient": ingredient,
            "uom": canonical_uom(uom),
            "actual_quantity": 0,
            "reserved_quantity": 0,
            "available_quantity": 0,
            "average_cost": flt(cost),
            "stock_value": 0,
            "count_status": "غير مجرود / Not Counted",
            "stock_source_note": NOTE,
        }
    )
    balance.insert(ignore_permissions=True)
    return balance


def execute():
    if not _ready():
        return

    # Prevent duplicate audit movements when migrate is retried after the patch
    # has already completed on this site.
    if frappe.db.exists(
        "WAFD Stock Movement",
        {"movement_type": "تسوية / Adjustment", "notes": ["like", f"%{REFERENCE_MARKER}%"]},
    ):
        return

    # Use one row per ingredient in each movement.  The master-data seed may
    # contain the same ingredient more than once (for example under multiple
    # recipes/categories), while WAFD Stock Movement deliberately rejects
    # duplicate ingredient rows.  Keep the largest configured minimum instead
    # of summing duplicates, because this patch establishes a target opening
    # balance rather than recording multiple receipts.
    grouped: dict[str, dict[str, dict]] = defaultdict(dict)

    for ingredient, _code, category, uom, cost, minimum_stock, _supplier in INGREDIENTS:
        if not frappe.db.exists("WAFD Ingredient", ingredient):
            continue
        warehouse = _preferred_warehouse(category)
        if not warehouse:
            continue

        balance = _ensure_balance(warehouse, ingredient, uom, cost)
        if flt(balance.actual_quantity) > 0:
            continue

        quantity = max(flt(minimum_stock), 1)
        candidate = {
            "ingredient": ingredient,
            "quantity": quantity,
            "uom": canonical_uom(uom),
            "unit_cost": flt(cost),
            "amount": quantity * flt(cost),
            "traceability_notes": NOTE,
        }
        existing = grouped[warehouse].get(ingredient)
        if not existing or flt(candidate["quantity"]) > flt(existing["quantity"]):
            grouped[warehouse][ingredient] = candidate

    for warehouse, item_map in grouped.items():
        items = list(item_map.values())
        movement = frappe.get_doc(
            {
                "doctype": "WAFD Stock Movement",
                "movement_type": "تسوية / Adjustment",
                "posting_date": now_datetime(),
                "target_warehouse": warehouse,
                "status": "مسودة / Draft",
                "notes": NOTE,
                "items": items,
            }
        )
        movement.insert(ignore_permissions=True)

        for row in movement.items:
            balance = _ensure_balance(warehouse, row.ingredient, row.uom, row.unit_cost)
            # Re-check under the same transaction to avoid overwriting stock that
            # may have been posted concurrently.
            if flt(balance.actual_quantity) > 0:
                continue
            balance.actual_quantity = flt(row.quantity)
            balance.average_cost = flt(row.unit_cost)
            balance.last_movement_date = movement.posting_date
            balance.stock_source_note = NOTE
            balance.count_status = "افتتاحي اختباري / Test Opening"
            balance.save(ignore_permissions=True)

        movement.db_set(
            {
                "status": "مرحلة / Posted",
                "posted_by": frappe.session.user or "Administrator",
                "posted_on": now_datetime(),
            },
            update_modified=True,
        )
