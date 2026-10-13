"""RC150: repair ingredient warehouse routing and legacy acceptance-test stock.

The migration is intentionally conservative:
- every ingredient's preferred warehouse is recalculated from the current
  operational storage rules;
- a zero balance placeholder is created in the corrected warehouse when needed;
- only RC50 acceptance-test opening stock is automatically moved out of an
  incorrect legacy warehouse, and that relocation is recorded as a posted
  transfer movement for auditability;
- real/user-entered stock in a different warehouse is never silently moved.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe.utils import flt, now_datetime

from wafd_one.master_data import preferred_warehouse_for_ingredient
from wafd_one.uom import canonical_uom

PATCH_MARKER = "RC150-WAREHOUSE-ROUTING-REPAIR"
RC50_MARKER = "RC50-ACCEPTANCE-OPENING-STOCK"


def _ready() -> bool:
    required = (
        "WAFD Ingredient",
        "WAFD Warehouse",
        "WAFD Stock Balance",
        "WAFD Stock Movement",
        "WAFD Stock Movement Item",
    )
    return all(frappe.db.exists("DocType", doctype) for doctype in required)


def _ensure_balance(warehouse: str, ingredient: str, uom: str | None, cost: float):
    name = frappe.db.get_value(
        "WAFD Stock Balance", {"warehouse": warehouse, "ingredient": ingredient}, "name"
    )
    if name:
        return frappe.get_doc("WAFD Stock Balance", name)
    return frappe.get_doc(
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
            "stock_source_note": f"{PATCH_MARKER} | Correct storage-zone placeholder.",
        }
    ).insert(ignore_permissions=True)


def _repair_preferred_warehouses():
    ingredient_meta = frappe.get_meta("WAFD Ingredient")
    has_preferred = ingredient_meta.has_field("preferred_warehouse")
    repaired = {}

    for row in frappe.get_all(
        "WAFD Ingredient",
        fields=["name", "ingredient_name", "category", "uom", "standard_cost", "latest_market_cost"],
    ):
        ingredient_name = row.ingredient_name or row.name
        preferred = preferred_warehouse_for_ingredient(ingredient_name, row.category)
        if not preferred or not frappe.db.exists("WAFD Warehouse", preferred):
            continue
        repaired[row.name] = preferred
        if has_preferred:
            current = frappe.db.get_value("WAFD Ingredient", row.name, "preferred_warehouse")
            if current != preferred:
                frappe.db.set_value(
                    "WAFD Ingredient", row.name, "preferred_warehouse", preferred, update_modified=False
                )
        _ensure_balance(
            preferred,
            row.name,
            row.uom,
            flt(row.latest_market_cost) or flt(row.standard_cost),
        )
    return repaired


def _move_legacy_acceptance_stock(repaired: dict[str, str]):
    """Transfer only RC50 acceptance-test balances that are in the wrong zone."""
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for ingredient, preferred in repaired.items():
        balances = frappe.get_all(
            "WAFD Stock Balance",
            filters={"ingredient": ingredient},
            fields=[
                "name", "warehouse", "actual_quantity", "reserved_quantity",
                "average_cost", "uom", "stock_source_note",
            ],
        )
        for balance in balances:
            source = balance.warehouse
            if not source or source == preferred:
                continue
            if RC50_MARKER not in (balance.stock_source_note or ""):
                continue
            available = max(flt(balance.actual_quantity) - flt(balance.reserved_quantity), 0)
            if available <= 0:
                continue
            grouped[(source, preferred)].append(
                {
                    "ingredient": ingredient,
                    "quantity": available,
                    "uom": balance.uom,
                    "unit_cost": flt(balance.average_cost),
                }
            )

    if not grouped:
        return []

    from wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement import post_movement

    posted = []
    for (source, target), items in grouped.items():
        # A patch retry must not duplicate an already-posted transfer.
        notes = f"{PATCH_MARKER} | {source} -> {target}"
        existing = frappe.db.get_value(
            "WAFD Stock Movement",
            {
                "movement_type": "تحويل / Transfer",
                "source_warehouse": source,
                "target_warehouse": target,
                "notes": notes,
            },
            "name",
        )
        if existing:
            continue

        movement = frappe.get_doc(
            {
                "doctype": "WAFD Stock Movement",
                "movement_type": "تحويل / Transfer",
                "posting_date": now_datetime(),
                "source_warehouse": source,
                "target_warehouse": target,
                "status": "مسودة / Draft",
                "notes": notes,
            }
        )
        for item in items:
            movement.append("items", item)
        movement.insert(ignore_permissions=True)
        result = post_movement(movement.name)
        if result.get("posted") or frappe.db.get_value(
            "WAFD Stock Movement", movement.name, "status"
        ) == "مرحلة / Posted":
            posted.append(movement.name)
    return posted


def _refresh_unstarted_batches():
    if not frappe.db.exists("DocType", "WAFD Production Batch"):
        return 0
    names = frappe.get_all(
        "WAFD Production Batch",
        filters={"status": "مخطط / Planned"},
        pluck="name",
    )
    refreshed = 0
    for name in names:
        # Never rewrite allocations that have already been posted/issued.
        posted_issue = frappe.db.sql(
            """
            select sm.name
              from `tabWAFD Stock Movement` sm
             where sm.production_batch=%s
               and sm.status='مرحلة / Posted'
               and sm.movement_type='صرف / Issue'
             limit 1
            """,
            (name,),
        )
        if posted_issue:
            continue
        try:
            batch = frappe.get_doc("WAFD Production Batch", name)
            batch.flags.ignore_version = True
            batch.save(ignore_permissions=True)
            refreshed += 1
        except Exception:
            # Migration must remain recoverable even if a legacy draft has some
            # unrelated validation issue.  The runtime allocator still fixes it
            # the next time the document is saved/refreshed.
            frappe.log_error(frappe.get_traceback(), f"{PATCH_MARKER}: {name}")
    return refreshed


def execute():
    if not _ready():
        return
    repaired = _repair_preferred_warehouses()
    _move_legacy_acceptance_stock(repaired)
    _refresh_unstarted_batches()
