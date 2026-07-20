"""Administrative utilities for WAFD ONE.

Destructive operations in this module are deliberately restricted to
Administrator, System Manager, and WAFD Operations Manager users and require an explicit confirmation
phrase from the client.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

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
def reset_demo_database(confirmation: str, reload_master_data: int | str = 1) -> dict:
    """Disabled permanently to protect production and reference data."""
    _check_admin_permission()
    frappe.throw(
        _("Destructive reset is disabled permanently. Use Install Master Data, which only adds missing records."),
        frappe.ValidationError,
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
def clear_reference_data(confirmation: str) -> dict:
    """Disabled permanently to prevent deletion of reference records."""
    _check_admin_permission()
    frappe.throw(
        _("Deleting reference data is disabled permanently. Existing data is protected."),
        frappe.ValidationError,
    )

