"""Administrative utilities for WAFD ONE.

Destructive operations in this module are deliberately restricted to
Administrator, System Manager, and WAFD Operations Manager users and require an explicit confirmation
phrase from the client.
"""

from __future__ import annotations

import json
import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from wafd_one.master_data import load_reference_master_data

CONFIRMATION_PHRASE = "RESET WAFD ONE"

# Child tables first, then operational transactions, then master data.
# frappe.db.delete is used intentionally for a full demo reset so circular links
# (Contract <-> Project) cannot block cleanup. User accounts, roles, metadata,
# settings and non-WAFD records are never included.
RESET_ORDER = [
    "WAFD Invoice Item",
    "WAFD Meal Plan Item",
    "WAFD Production Material",
    "WAFD Purchase Order Item",
    "WAFD Recipe Item",
    "WAFD Stock Movement Item",
    "WAFD Project Hotel",
    "WAFD Project Service",
    "WAFD Delivery Proof",
    "WAFD Complaint",
    "WAFD Payment",
    "WAFD Invoice",
    "WAFD Project Revenue",
    "WAFD Project Cost",
    "WAFD Delivery Trip",
    "WAFD Loading Record",
    "WAFD Packaging Record",
    "WAFD Quality Inspection",
    "WAFD Production Batch",
    "WAFD Stock Movement",
    "WAFD Purchase Order",
    "WAFD Daily Meal Plan",
    "WAFD Meal Plan",
    "WAFD Contract",
    "WAFD Catering Project",
    "WAFD Stock Balance",
    "WAFD Recipe",
    "WAFD Ingredient",
    "WAFD Supplier",
    "WAFD Warehouse",
    "WAFD Vehicle",
    "WAFD Driver",
    "WAFD Hotel",
    "WAFD Mission",
]

REFERENCE_DOCTYPES = [
    "WAFD Stock Balance",
    "WAFD Recipe",
    "WAFD Ingredient",
    "WAFD Supplier",
    "WAFD Warehouse",
    "WAFD Hotel",
    "WAFD Mission",
]


def _check_admin_permission() -> None:
    user = frappe.session.user
    roles = set(frappe.get_roles(user))
    if user != "Administrator" and not ({"System Manager", "WAFD Operations Manager"} & roles):
        frappe.throw(
            _("Only Administrator, System Manager, or WAFD Operations Manager can use WAFD administration tools."),
            frappe.PermissionError,
        )


def _existing_doctypes(doctypes: list[str]) -> list[str]:
    return [doctype for doctype in doctypes if frappe.db.exists("DocType", doctype)]


def _counts(doctypes: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for doctype in _existing_doctypes(doctypes):
        result[doctype] = int(frappe.db.count(doctype))
    return result


@frappe.whitelist()
def get_database_summary() -> dict:
    """Return record counts shown before a reset."""
    _check_admin_permission()
    counts = _counts(RESET_ORDER)
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "confirmation_phrase": CONFIRMATION_PHRASE,
    }


def _delete_doctypes(doctypes: list[str]) -> dict[str, int]:
    deleted: dict[str, int] = {}
    for doctype in _existing_doctypes(doctypes):
        count = int(frappe.db.count(doctype))
        if count:
            frappe.db.delete(doctype)
        deleted[doctype] = count
    return deleted


@frappe.whitelist(methods=["POST"])
def reset_demo_database(confirmation: str = "", reload_master_data: int | str = 1) -> dict:
    """Legacy endpoint retained only to prevent accidental destructive resets.

    From v6.2.0 this action never deletes data. Existing sites or cached clients
    that still call the old method receive a clear error and must use the safe
    missing-master-data installer instead.
    """
    _check_admin_permission()
    frappe.throw(
        _("Data reset has been permanently disabled to protect hotels, recipes, projects, and operational records. Use Install Missing Master Data instead."),
        title=_("Protected operation"),
    )


@frappe.whitelist(methods=["POST"])
def install_master_data() -> dict:
    """Install only missing reference data without deleting operations."""
    _check_admin_permission()
    try:
        created = load_reference_master_data()
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "WAFD ONE master data installation failed")
        raise
    return {
        "created": created,
        "created_total": sum(created.values()),
        "message": _("WAFD ONE master data was installed successfully."),
    }


@frappe.whitelist(methods=["POST"])
def clear_reference_data(confirmation: str = "") -> dict:
    """Legacy endpoint permanently disabled from v6.3.0.

    Kept only so cached clients cannot invoke an older destructive action.
    """
    _check_admin_permission()
    frappe.throw(
        _("Reference-data deletion has been permanently disabled. Hotels, recipes, ingredients, and all operational records are protected."),
        title=_("Protected operation"),
    )



GO_LIVE_CONFIRMATION_PHRASE = "PREPARE WAFD GO LIVE"


def _inventory_go_live_state():
    prepared = cint(frappe.db.get_single_value("WAFD Administration Console", "go_live_inventory_prepared") or 0)
    balances = frappe.get_all("WAFD Stock Balance", fields=["name", "warehouse", "ingredient", "uom", "actual_quantity", "reserved_quantity", "available_quantity", "average_cost", "stock_value", "count_status", "physical_count_date", "last_movement_date", "stock_source_note"])
    nonzero = [row for row in balances if abs(flt(row.actual_quantity)) > 0.000001 or abs(flt(row.reserved_quantity)) > 0.000001 or abs(flt(row.stock_value)) > 0.000001]
    movements = frappe.get_all("WAFD Stock Movement", filters={"is_pre_go_live_test": 0}, fields=["name", "movement_type", "posting_date", "project", "production_batch", "source_warehouse", "target_warehouse", "status", "total_amount", "reference_type", "reference_name"])
    return {"prepared": prepared, "balances": balances, "nonzero": nonzero, "movements": movements}


@frappe.whitelist()
def preview_go_live_inventory_reset() -> dict:
    _check_admin_permission()
    state = _inventory_go_live_state()
    return {
        "already_prepared": state["prepared"],
        "balance_count": len(state["balances"]),
        "nonzero_balance_count": len(state["nonzero"]),
        "movement_count": len(state["movements"]),
        "posted_movement_count": sum(1 for row in state["movements"] if row.status == "مرحلة / Posted"),
        "stock_value": sum(flt(row.stock_value) for row in state["balances"]),
        "confirmation_phrase": GO_LIVE_CONFIRMATION_PHRASE,
    }


@frappe.whitelist(methods=["POST"])
def prepare_inventory_for_go_live(confirmation: str = "") -> dict:
    """Archive test stock history and zero current balances without deleting masters.

    This is intentionally one-way at the application level. A complete JSON
    snapshot is stored in WAFD Inventory Reset Log before any quantities change.
    """
    _check_admin_permission()
    if confirmation != GO_LIVE_CONFIRMATION_PHRASE:
        frappe.throw(_("Confirmation phrase does not match."), title=_("Go-Live confirmation required"))
    state = _inventory_go_live_state()
    if state["prepared"]:
        frappe.throw(_("Inventory Go-Live preparation was already completed. It cannot be run twice."), title=_("Protected operation"))

    now = now_datetime()
    snapshot = frappe.get_doc({
        "doctype": "WAFD Inventory Reset Log",
        "reset_at": now,
        "reset_by": frappe.session.user,
        "balance_count": len(state["balances"]),
        "movement_count": len(state["movements"]),
        "stock_value_before": sum(flt(row.stock_value) for row in state["balances"]),
        "balances_snapshot": json.dumps([dict(row) for row in state["balances"]], ensure_ascii=False, default=str),
        "movements_snapshot": json.dumps([dict(row) for row in state["movements"]], ensure_ascii=False, default=str),
        "notes": "Pre-Go-Live test inventory archived; master data preserved. Enter real opening balances through approved stock adjustments.",
    })
    snapshot.insert(ignore_permissions=True)

    frappe.db.sql("""update `tabWAFD Stock Movement`
                       set is_pre_go_live_test=1
                     where coalesce(is_pre_go_live_test,0)=0""")
    frappe.db.sql("""update `tabWAFD Stock Balance`
                       set actual_quantity=0,
                           reserved_quantity=0,
                           available_quantity=0,
                           average_cost=0,
                           stock_value=0,
                           last_movement_date=NULL,
                           physical_count_date=NULL,
                           count_status='غير مجرود / Not Counted',
                           stock_source_note='Go-Live reset: test quantity archived; enter approved opening count.'""")
    frappe.db.set_single_value("WAFD Administration Console", "go_live_inventory_prepared", 1)
    frappe.db.set_single_value("WAFD Administration Console", "go_live_prepared_on", now)
    frappe.db.set_single_value("WAFD Administration Console", "go_live_prepared_by", frappe.session.user)
    frappe.db.commit()
    frappe.clear_cache(doctype="WAFD Stock Balance")
    frappe.clear_cache(doctype="WAFD Stock Movement")
    return {
        "snapshot": snapshot.name,
        "balances_reset": len(state["balances"]),
        "movements_archived": len(state["movements"]),
        "message": _("Inventory test quantities were safely archived and reset. Master data was preserved."),
    }
