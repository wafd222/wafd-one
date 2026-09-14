"""Behaviour test for one shared departure across a vehicle meal run."""

from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
import importlib.util
import sys


updates = []
captured_filters = {}
first_departure = datetime(2026, 9, 13, 18, 15, 44)
rows = [
    SimpleNamespace(name="TRIP-1", status="تم التسليم / Delivered", actual_departure=first_departure,
                    driver_accepted_on=first_departure, planned_arrival=datetime(2026, 9, 13, 18, 30),
                    loading_record=None, driver="Mustanser", assigned_driver_user="driver@example.com"),
    SimpleNamespace(name="TRIP-2", status="مخططة / Planned", actual_departure=None,
                    driver_accepted_on=None, planned_arrival=datetime(2026, 9, 13, 18, 45),
                    loading_record=None, driver="Mustanser", assigned_driver_user="driver@example.com"),
    SimpleNamespace(name="TRIP-3", status="مخططة / Planned", actual_departure=None,
                    driver_accepted_on=None, planned_arrival=datetime(2026, 9, 13, 19, 0),
                    loading_record=None, driver="Mustanser", assigned_driver_user="driver@example.com"),
]

frappe = ModuleType("frappe")
frappe.session = SimpleNamespace(user="driver@example.com")
frappe.PermissionError = PermissionError
frappe._ = lambda value: value
frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn) if not args else args[0]
frappe.get_roles = lambda user=None: ["WAFD Driver"]


def get_all(doctype, filters=None, **kwargs):
    assert doctype == "WAFD Delivery Trip"
    captured_filters.update(filters or {})
    return rows


frappe.get_all = get_all
frappe.get_doc = lambda doctype, name: SimpleNamespace(notify_update=lambda: None)
frappe.throw = lambda message, *args: (_ for _ in ()).throw(RuntimeError(message))
frappe.db = SimpleNamespace(
    get_value=lambda *args, **kwargs: None,
    exists=lambda *args, **kwargs: False,
    set_value=lambda doctype, name, values, **kwargs: updates.append((doctype, name, values)),
)

utils = ModuleType("frappe.utils")
utils.cint = lambda value: int(value or 0)
utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
utils.now_datetime = lambda: datetime(2026, 9, 13, 20, 0, 0)
sys.modules["frappe"] = frappe
sys.modules["frappe.utils"] = utils

security = ModuleType("wafd_one.driver_security")
security.get_drivers_for_user = lambda user: ["Mustanser"]
security.repair_trip_assignments = lambda user: None
security.trip_is_assigned_to_user = lambda driver, assigned, user: assigned == user
security.trips_for_user = lambda trips, user: trips
sys.modules["wafd_one.driver_security"] = security

employee = ModuleType("wafd_one.employee_team")
employee._normalize_mobile = lambda value: value
sys.modules["wafd_one.employee_team"] = employee

reconciliation = ModuleType("wafd_one.delivery_reconciliation")
reconciliation.reconcile_missing_delivery_trips = lambda **kwargs: {"counts": {}, "results": []}
sys.modules["wafd_one.delivery_reconciliation"] = reconciliation

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("driver_portal_rc291_test", root / "wafd_one/driver_portal.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

trip = SimpleNamespace(
    name="TRIP-2", trip_date="2026-09-13", driver="Mustanser", vehicle="5190",
    meal_type="إفطار / Breakfast",
)
departure, names = module._start_delivery_run(trip)

assert departure == first_departure
assert names == ["TRIP-2", "TRIP-3"]
assert captured_filters["trip_date"] == "2026-09-13"
assert captured_filters["driver"] == "Mustanser"
assert captured_filters["vehicle"] == "5190"
assert captured_filters["meal_type"] == "إفطار / Breakfast"
trip_updates = {name: values for doctype, name, values in updates if doctype == "WAFD Delivery Trip"}
assert set(trip_updates) == {"TRIP-2", "TRIP-3"}
assert all(values["actual_departure"] == first_departure for values in trip_updates.values())
assert all(values["driver_accepted_on"] == first_departure for values in trip_updates.values())
assert all(values["status"] == "في الطريق / In Transit" for values in trip_updates.values())
print("RC291 shared departure behaviour test passed")
