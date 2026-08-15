"""Row-level access controls for WAFD drivers.

Drivers can only list/open trips and delivery proofs assigned to the WAFD Driver
record linked to their current System User. Management roles retain their normal
role-based access.
"""
import frappe

DRIVER_ROLE = "WAFD Driver"
BYPASS_ROLES = {
    "System Manager",
    "WAFD Operations Manager",
    "WAFD Delivery Supervisor",
    "WAFD Project Manager",
}


def _user(user=None):
    return user or frappe.session.user


def _roles(user):
    return set(frappe.get_roles(user))


def _is_scoped_driver(user):
    if user == "Administrator":
        return False
    roles = _roles(user)
    return DRIVER_ROLE in roles and not (roles & BYPASS_ROLES)


def get_driver_for_user(user=None):
    user = _user(user)
    if not user or user in ("Guest", "Administrator"):
        return None
    return frappe.db.get_value("WAFD Driver", {"system_user": user}, "name")


def delivery_trip_query(user=None):
    user = _user(user)
    if not _is_scoped_driver(user):
        return ""
    driver = get_driver_for_user(user)
    if not driver:
        return "1=0"
    return "`tabWAFD Delivery Trip`.`driver` = {driver}".format(driver=frappe.db.escape(driver))


def delivery_trip_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = _user(user)
    if not _is_scoped_driver(user):
        return True
    if (ptype or permission_type) == "create":
        return False
    driver = get_driver_for_user(user)
    return bool(driver and doc.driver == driver)


def delivery_proof_query(user=None):
    user = _user(user)
    if not _is_scoped_driver(user):
        return ""
    driver = get_driver_for_user(user)
    if not driver:
        return "1=0"
    driver_sql = frappe.db.escape(driver)
    return (
        "exists (select 1 from `tabWAFD Delivery Trip` dt "
        "where dt.name = `tabWAFD Delivery Proof`.`delivery_trip` "
        f"and dt.driver = {driver_sql})"
    )


def delivery_proof_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = _user(user)
    if not _is_scoped_driver(user):
        return True
    trip_driver = frappe.db.get_value("WAFD Delivery Trip", doc.delivery_trip, "driver") if doc.delivery_trip else None
    driver = get_driver_for_user(user)
    return bool(driver and trip_driver == driver)
