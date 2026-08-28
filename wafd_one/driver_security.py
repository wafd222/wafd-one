"""Row-level access controls for WAFD drivers.

Drivers can only list/open trips and delivery proofs assigned to the WAFD Driver
record linked to their current System User. Older, unlinked duplicate driver
records are also recognised when they carry the same normalized mobile number.
Management roles retain their normal role-based access.
"""
import re

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


def _mobile_key(value):
    """Return a comparison-only mobile key without raising validation errors."""
    value = str(value or "").strip().translate(
        str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    )
    digits = re.sub(r"\D", "", value)
    if re.fullmatch(r"05\d{8}", digits):
        return f"966{digits[1:]}"
    if re.fullmatch(r"009665\d{8}", digits):
        return digits[2:]
    if re.fullmatch(r"9665\d{8}", digits):
        return digits
    return digits.lstrip("0") if 8 <= len(digits.lstrip("0")) <= 15 else ""


def _name_key(value):
    return " ".join(str(value or "").split()).casefold()


def _base_driver_name(row):
    """Remove the collision suffix used when a duplicate driver is created."""
    value = _name_key(row.driver_name or row.name)
    user = str(row.system_user or "").strip()
    if user and "@" in user:
        suffix = _name_key(f" - {user.split('@', 1)[0]}")
        if value.endswith(suffix):
            value = value[: -len(suffix)].strip()
    return value


def _driver_rows():
    return frappe.get_all(
        "WAFD Driver",
        fields=["name", "driver_name", "system_user", "mobile", "creation"],
        order_by="creation asc",
    )


def get_drivers_for_user(user=None):
    """Return canonical and safe legacy driver records for one login.

    A legacy alias must be unlinked and share the exact normalized mobile number
    with a record explicitly linked to the current user. A record linked to any
    other user is never included, even if its name or mobile matches.
    """
    user = _user(user)
    if not user or user in ("Guest", "Administrator"):
        return []

    rows = _driver_rows()
    linked = [row for row in rows if row.system_user == user]
    if not linked:
        return []

    identities = {
        (_base_driver_name(row), _mobile_key(row.mobile))
        for row in linked
        if _base_driver_name(row) and _mobile_key(row.mobile)
    }
    identities_claimed_by_others = {
        (_base_driver_name(row), _mobile_key(row.mobile))
        for row in rows
        if row.system_user
        and row.system_user != user
        and _base_driver_name(row)
        and _mobile_key(row.mobile)
    }
    identities -= identities_claimed_by_others
    drivers = [row.name for row in linked]
    for row in rows:
        if row.system_user or row.name in drivers:
            continue
        if (_base_driver_name(row), _mobile_key(row.mobile)) in identities:
            drivers.append(row.name)
    return list(dict.fromkeys(drivers))


def get_driver_for_user(user=None):
    drivers = get_drivers_for_user(user)
    return drivers[0] if drivers else None


def resolve_linked_driver(driver_name):
    """Resolve an unlinked legacy driver to its unique enabled login record."""
    if not driver_name:
        return None, None
    rows = _driver_rows()
    selected = next((row for row in rows if row.name == driver_name), None)
    if not selected:
        return None, None
    if selected.system_user:
        return selected.name, selected.system_user

    identity = (_base_driver_name(selected), _mobile_key(selected.mobile))
    if not all(identity):
        return None, None
    candidates = []
    for row in rows:
        if not row.system_user or (_base_driver_name(row), _mobile_key(row.mobile)) != identity:
            continue
        if frappe.db.get_value("User", row.system_user, "enabled"):
            candidates.append((row.name, row.system_user))
    return candidates[0] if len(candidates) == 1 else (None, None)


def _sql_in(values):
    return ", ".join(frappe.db.escape(value) for value in values)


def delivery_trip_query(user=None):
    user = _user(user)
    if not _is_scoped_driver(user):
        return ""
    drivers = get_drivers_for_user(user)
    if not drivers:
        return "1=0"
    return f"`tabWAFD Delivery Trip`.`driver` in ({_sql_in(drivers)})"


def delivery_trip_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = _user(user)
    if not _is_scoped_driver(user):
        return True
    if (ptype or permission_type) == "create":
        return False
    return bool(doc.driver and doc.driver in get_drivers_for_user(user))


def delivery_proof_query(user=None):
    user = _user(user)
    if not _is_scoped_driver(user):
        return ""
    drivers = get_drivers_for_user(user)
    if not drivers:
        return "1=0"
    return (
        "exists (select 1 from `tabWAFD Delivery Trip` dt "
        "where dt.name = `tabWAFD Delivery Proof`.`delivery_trip` "
        f"and dt.driver in ({_sql_in(drivers)}))"
    )


def delivery_proof_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = _user(user)
    if not _is_scoped_driver(user):
        return True
    trip_driver = frappe.db.get_value("WAFD Delivery Trip", doc.delivery_trip, "driver") if doc.delivery_trip else None
    return bool(trip_driver and trip_driver in get_drivers_for_user(user))
