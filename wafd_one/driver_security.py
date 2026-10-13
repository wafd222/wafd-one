"""Stable row-level access controls for WAFD delivery users.

The durable assignment is ``WAFD Delivery Trip.assigned_driver_user``. Driver
profile matching remains only as a migration and compatibility bridge for
legacy trips created before that field existed.
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


def _enabled_driver_user(user):
    return bool(
        user
        and frappe.db.get_value("User", user, "enabled")
        and DRIVER_ROLE in _roles(user)
    )


def _unique(values):
    values = list(dict.fromkeys(value for value in values if value))
    return values[0] if len(values) == 1 else None


def _user_for_driver(driver_name, rows):
    selected = next((row for row in rows if row.name == driver_name), None)
    if not selected:
        return None
    if selected.system_user and _enabled_driver_user(selected.system_user):
        return selected.system_user

    linked = [row for row in rows if row.system_user and _enabled_driver_user(row.system_user)]
    selected_identity = (_base_driver_name(selected), _mobile_key(selected.mobile))
    if all(selected_identity):
        strict = _unique(
            row.system_user
            for row in linked
            if (_base_driver_name(row), _mobile_key(row.mobile)) == selected_identity
        )
        if strict:
            return strict

    # Older manually-created profiles can carry a stale mobile. An exact and
    # unique driver name remains deterministic and does not widen access.
    selected_name = _base_driver_name(selected)
    by_linked_name = _unique(
        row.system_user for row in linked if selected_name and _base_driver_name(row) == selected_name
    )
    if by_linked_name:
        return by_linked_name

    # Final compatibility bridge for a driver that predates linked profiles.
    # It is accepted only when one enabled Driver user has the exact full name.
    matching_users = []
    for user_row in frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name"],
    ):
        if selected_name and _name_key(user_row.full_name) == selected_name and _enabled_driver_user(user_row.name):
            matching_users.append(user_row.name)
    return _unique(matching_users)


def get_user_for_driver(driver_name):
    """Resolve one driver profile to exactly one enabled Driver user."""
    if not driver_name:
        return None
    # Some early imports used the login itself as the driver identifier. Keep
    # that deterministic legacy shape working without broadening access.
    if _enabled_driver_user(driver_name):
        return driver_name
    return _user_for_driver(driver_name, _driver_rows())


def get_drivers_for_user(user=None):
    """Return every canonical/legacy driver profile owned by one login."""
    user = _user(user)
    if not user or user in ("Guest", "Administrator") or not _enabled_driver_user(user):
        return []
    rows = _driver_rows()
    drivers = [row.name for row in rows if row.system_user == user]
    for row in rows:
        if row.name in drivers:
            continue
        # Never reassign a profile owned by another enabled Driver account.
        # A profile linked only to a disabled/obsolete account can be migrated.
        if row.system_user and _enabled_driver_user(row.system_user):
            continue
        if _user_for_driver(row.name, rows) == user:
            drivers.append(row.name)
    return list(dict.fromkeys(drivers))


def get_driver_for_user(user=None):
    drivers = get_drivers_for_user(user)
    return drivers[0] if drivers else None


def resolve_linked_driver(driver_name):
    """Return the canonical driver profile and its enabled login."""
    if not driver_name:
        return None, None
    rows = _driver_rows()
    selected = next((row for row in rows if row.name == driver_name), None)
    if not selected:
        return None, None
    user = _user_for_driver(driver_name, rows)
    if not user:
        return None, None
    if selected.system_user == user:
        return selected.name, user
    canonical = next((row.name for row in rows if row.system_user == user), None)
    return (canonical, user) if canonical else (None, None)


def repair_trip_assignments(user=None):
    """Backfill the explicit login assignment on legacy delivery trips.

    RC245 handled only NULL assignments. A migrated site can also contain an
    obsolete disabled login in the new column (for example after recreating an
    employee account). Replace only missing/disabled assignments; an enabled
    assignment to another driver is never overridden automatically.
    """
    if not frappe.db.has_column("WAFD Delivery Trip", "assigned_driver_user"):
        return 0
    repaired = 0
    for trip in frappe.get_all(
        "WAFD Delivery Trip",
        fields=["name", "driver", "assigned_driver_user"],
    ):
        if trip.assigned_driver_user and _enabled_driver_user(trip.assigned_driver_user):
            continue
        driver_user = get_user_for_driver(trip.driver)
        if not driver_user or (user and driver_user != user):
            continue
        frappe.db.set_value(
            "WAFD Delivery Trip", trip.name, "assigned_driver_user", driver_user, update_modified=False
        )
        repaired += 1
    return repaired


def trips_for_user(trips, user=None):
    """Securely filter already-fetched trip rows for one driver login.

    This intentionally avoids combining Frappe ``filters`` and ``or_filters``.
    The caller may fetch with ``get_all`` only because every row is filtered
    here before it is returned to the client.
    """
    user = _user(user)
    drivers = set(get_drivers_for_user(user))
    matched = []
    for trip in trips:
        assigned = getattr(trip, "assigned_driver_user", None)
        driver = getattr(trip, "driver", None)
        if assigned == user or (driver and driver in drivers):
            matched.append(trip)
            continue
        # Resolve a legacy identifier directly as a final deterministic bridge.
        if driver and get_user_for_driver(driver) == user:
            matched.append(trip)
    return matched


def trip_is_assigned_to_user(driver, assigned_driver_user, user=None):
    user = _user(user)
    if assigned_driver_user == user:
        return True
    return bool(driver and driver in get_drivers_for_user(user))


def _sql_in(values):
    return ", ".join(frappe.db.escape(value) for value in values)


def delivery_trip_query(user=None):
    user = _user(user)
    if not _is_scoped_driver(user):
        return ""
    drivers = get_drivers_for_user(user)
    clauses = [f"`tabWAFD Delivery Trip`.`assigned_driver_user` = {frappe.db.escape(user)}"]
    if drivers:
        clauses.append(f"`tabWAFD Delivery Trip`.`driver` in ({_sql_in(drivers)})")
    return "(" + " or ".join(clauses) + ")"


def delivery_trip_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = _user(user)
    if not _is_scoped_driver(user):
        return True
    if (ptype or permission_type) == "create":
        return False
    return trip_is_assigned_to_user(doc.driver, getattr(doc, "assigned_driver_user", None), user)


def delivery_proof_query(user=None):
    user = _user(user)
    if not _is_scoped_driver(user):
        return ""
    drivers = get_drivers_for_user(user)
    clauses = [f"dt.assigned_driver_user = {frappe.db.escape(user)}"]
    if drivers:
        clauses.append(f"dt.driver in ({_sql_in(drivers)})")
    return (
        "exists (select 1 from `tabWAFD Delivery Trip` dt "
        "where dt.name = `tabWAFD Delivery Proof`.`delivery_trip` and ("
        + " or ".join(clauses)
        + "))"
    )


def delivery_proof_has_permission(doc, user=None, ptype=None, permission_type=None, **kwargs):
    user = _user(user)
    if not _is_scoped_driver(user):
        return True
    if not doc.delivery_trip:
        return False
    trip = frappe.db.get_value(
        "WAFD Delivery Trip", doc.delivery_trip, ["driver", "assigned_driver_user"], as_dict=True
    )
    return bool(trip and trip_is_assigned_to_user(trip.driver, trip.assigned_driver_user, user))
