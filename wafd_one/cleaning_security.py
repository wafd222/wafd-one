"""Least-privilege access controls for cleaning inventory."""
import frappe

ROLE = "WAFD Cleaning Supervisor"
ELEVATED = {"System Manager", "WAFD Operations Manager", "WAFD Storekeeper"}
CLEANING_TYPE = "نظافة / Cleaning"


def _roles(user):
    return set(frappe.get_roles(user or frappe.session.user))


def _restricted(user):
    roles = _roles(user)
    return ROLE in roles and not (roles & ELEVATED)


def _cleaning_warehouse_names():
    return frappe.get_all("WAFD Warehouse", filters={"warehouse_type": CLEANING_TYPE}, pluck="name")


def warehouse_query(user=None):
    user = user or frappe.session.user
    if not _restricted(user): return ""
    return "`tabWAFD Warehouse`.`warehouse_type` = {}".format(frappe.db.escape(CLEANING_TYPE))


def stock_balance_query(user=None):
    user = user or frappe.session.user
    if not _restricted(user): return ""
    names = _cleaning_warehouse_names()
    if not names: return "1=0"
    vals = ",".join(frappe.db.escape(x) for x in names)
    return f"`tabWAFD Stock Balance`.`warehouse` in ({vals})"


def stock_movement_query(user=None):
    user = user or frappe.session.user
    if not _restricted(user): return ""
    names = _cleaning_warehouse_names()
    if not names: return "1=0"
    vals = ",".join(frappe.db.escape(x) for x in names)
    return ("`tabWAFD Stock Movement`.`movement_type`='صرف / Issue' "
            "and coalesce(`tabWAFD Stock Movement`.`is_pre_go_live_test`,0)=0 "
            f"and `tabWAFD Stock Movement`.`source_warehouse` in ({vals}) "
            f"and `tabWAFD Stock Movement`.`issued_to_user`={frappe.db.escape(user)}")


def warehouse_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = user or frappe.session.user
    if not _restricted(user): return True
    perm = ptype or permission_type
    if perm not in (None, "read", "select", "print", "report"): return False
    return doc.warehouse_type == CLEANING_TYPE


def stock_balance_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = user or frappe.session.user
    if not _restricted(user): return True
    perm = ptype or permission_type
    if perm not in (None, "read", "select", "print", "report"): return False
    return frappe.db.get_value("WAFD Warehouse", doc.warehouse, "warehouse_type") == CLEANING_TYPE


def stock_movement_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = user or frappe.session.user
    if not _restricted(user): return True
    perm = ptype or permission_type
    if perm not in (None, "read", "select", "print", "report"): return False
    return bool(not doc.get("is_pre_go_live_test") and doc.movement_type == "صرف / Issue" and doc.issued_to_user == user and frappe.db.get_value("WAFD Warehouse", doc.source_warehouse, "warehouse_type") == CLEANING_TYPE)
