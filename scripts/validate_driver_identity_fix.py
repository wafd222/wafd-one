"""Regression checks for RC245 explicit driver-user trip assignment."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True


class Row(dict):
    __getattr__ = dict.get


CURRENT_USER = "wafd.almadinah7@gmail.com"
OTHER_USER = "other@example.com"
DISABLED_USER = "old-driver@example.com"
DRIVERS = [
    Row(
        name="عمر - wafd.almadinah7",
        driver_name="عمر - wafd.almadinah7",
        system_user=CURRENT_USER,
        mobile="+966547726406",
        creation="2026-08-28 18:00:00",
    ),
    # Legacy profile has the correct unique name but a stale mobile. RC244 did
    # not resolve this case; RC245 must migrate it to the explicit user field.
    Row(
        name="عمر",
        driver_name="عمر",
        system_user=DISABLED_USER,
        mobile="0500000000",
        creation="2026-01-01 00:00:00",
    ),
    Row(
        name="سالم",
        driver_name="سالم",
        system_user=None,
        mobile="0547726406",
        creation="2026-01-02 00:00:00",
    ),
    Row(
        name="عمر آخر",
        driver_name="عمر آخر",
        system_user=OTHER_USER,
        mobile="0547726406",
        creation="2026-01-03 00:00:00",
    ),
]
USERS = [
    Row(name=CURRENT_USER, full_name="عمر", enabled=1, user_type="System User"),
    Row(name=OTHER_USER, full_name="عمر آخر", enabled=1, user_type="System User"),
    Row(name=DISABLED_USER, full_name="عمر", enabled=0, user_type="System User"),
]
TRIPS = {
    "TRIP-1": Row(
        name="TRIP-1", driver="عمر", assigned_driver_user=None
    ),
    "TRIP-2": Row(
        name="TRIP-2", driver="سالم", assigned_driver_user=CURRENT_USER
    ),
    "TRIP-3": Row(
        name="TRIP-3", driver="عمر", assigned_driver_user=DISABLED_USER
    ),
    "TRIP-4": Row(
        name="TRIP-4", driver="عمر آخر", assigned_driver_user=OTHER_USER
    ),
}


class FakeDB:
    @staticmethod
    def escape(value):
        return "'" + str(value).replace("'", "''") + "'"

    @staticmethod
    def has_column(doctype, field):
        return doctype == "WAFD Delivery Trip" and field == "assigned_driver_user"

    @staticmethod
    def get_value(doctype, name, field, as_dict=False):
        if doctype == "User" and field == "enabled":
            row = next((item for item in USERS if item.name == name), None)
            return row.enabled if row else None
        if doctype == "WAFD Delivery Trip":
            row = TRIPS.get(name)
            if not row:
                return None
            if isinstance(field, list):
                result = Row({key: row.get(key) for key in field})
                return result if as_dict else tuple(result[key] for key in field)
            return row.get(field)
        return None

    @staticmethod
    def set_value(doctype, name, field, value, update_modified=False):
        assert doctype == "WAFD Delivery Trip"
        TRIPS[name][field] = value


def get_all(doctype, filters=None, fields=None, order_by=None, **kwargs):
    if doctype == "WAFD Driver":
        return DRIVERS
    if doctype == "User":
        return USERS
    if doctype == "WAFD Delivery Trip":
        return list(TRIPS.values())
    return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.session = types.SimpleNamespace(user=CURRENT_USER)
fake_frappe.db = FakeDB()
fake_frappe.get_roles = lambda user=None: ["WAFD Driver"]
fake_frappe.get_all = get_all

sys.modules["frappe"] = fake_frappe
module_path = Path(__file__).resolve().parents[1] / "wafd_one" / "driver_security.py"
spec = importlib.util.spec_from_file_location("rc245_driver_security", module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

drivers = module.get_drivers_for_user(CURRENT_USER)
assert drivers == ["عمر - wafd.almadinah7", "عمر"], drivers
assert "سالم" not in drivers
assert "عمر آخر" not in drivers

resolved = module.resolve_linked_driver("عمر")
assert resolved == ("عمر - wafd.almadinah7", CURRENT_USER), resolved

assert module.get_user_for_driver(CURRENT_USER) == CURRENT_USER
assert module.repair_trip_assignments(CURRENT_USER) == 2
assert TRIPS["TRIP-1"].assigned_driver_user == CURRENT_USER
assert TRIPS["TRIP-3"].assigned_driver_user == CURRENT_USER
assert TRIPS["TRIP-4"].assigned_driver_user == OTHER_USER

visible = module.trips_for_user(list(TRIPS.values()), CURRENT_USER)
assert [row.name for row in visible] == ["TRIP-1", "TRIP-2", "TRIP-3"], visible

trip_sql = module.delivery_trip_query(CURRENT_USER)
assert "assigned_driver_user" in trip_sql and CURRENT_USER in trip_sql
assert module.delivery_trip_has_permission(TRIPS["TRIP-1"], CURRENT_USER)
assert module.delivery_trip_has_permission(TRIPS["TRIP-2"], CURRENT_USER)
assert not module.delivery_trip_has_permission(Row(driver="سالم", assigned_driver_user=None), CURRENT_USER)
assert module.delivery_proof_has_permission(Row(delivery_trip="TRIP-1"), CURRENT_USER)

print("RC247 deterministic driver assignment validation passed")
