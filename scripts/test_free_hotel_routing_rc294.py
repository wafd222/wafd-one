"""Behaviour tests for meal-run sequencing without hotel-order locking."""

from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
import importlib.util
import sys


frappe = ModuleType("frappe")
frappe.session = SimpleNamespace(user="driver@example.com")
frappe.PermissionError = PermissionError
frappe._ = lambda value: value
frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn) if not args else args[0]
frappe.get_roles = lambda user=None: ["WAFD Driver"]
frappe.throw = lambda message, *args: (_ for _ in ()).throw(RuntimeError(message))
frappe.db = SimpleNamespace()
utils = ModuleType("frappe.utils")
utils.cint = lambda value: int(value or 0)
utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
utils.now_datetime = lambda: datetime(2026, 9, 14, 5, 0, 0)
sys.modules["frappe"] = frappe
sys.modules["frappe.utils"] = utils

security = ModuleType("wafd_one.driver_security")
security.get_drivers_for_user = lambda user: ["DRIVER-1"]
security.repair_trip_assignments = lambda user: None
security.trip_is_assigned_to_user = lambda driver, assigned, user: True
security.trips_for_user = lambda rows, user: rows
sys.modules["wafd_one.driver_security"] = security

employee = ModuleType("wafd_one.employee_team")
employee._normalize_mobile = lambda value, required=False: value
sys.modules["wafd_one.employee_team"] = employee

reconciliation = ModuleType("wafd_one.delivery_reconciliation")
reconciliation.reconcile_missing_delivery_trips = lambda **kwargs: {"counts": {}, "results": []}
sys.modules["wafd_one.delivery_reconciliation"] = reconciliation

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("driver_portal_rc294_test", root / "wafd_one/driver_portal.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def trip(name, meal, planned):
    return SimpleNamespace(
        name=name, trip_date="2026-09-14", driver="DRIVER-1", vehicle="5190",
        meal_type=meal, planned_arrival=datetime.fromisoformat(planned),
    )


breakfast_1 = trip("BREAKFAST-1", "إفطار / Breakfast", "2026-09-14 06:00:00")
breakfast_2 = trip("BREAKFAST-2", "إفطار / Breakfast", "2026-09-14 06:15:00")
lunch_1 = trip("LUNCH-1", "غداء / Lunch", "2026-09-14 12:00:00")
rows = [breakfast_1, breakfast_2, lunch_1]

metadata = module._sequence_metadata(rows, set(), datetime(2026, 9, 14, 5, 0, 0))
assert metadata["BREAKFAST-1"]["sequence_state"] == "active"
assert metadata["BREAKFAST-2"]["sequence_state"] == "active"
assert metadata["BREAKFAST-1"]["sequence_actionable"] is True
assert metadata["BREAKFAST-2"]["sequence_actionable"] is True
assert metadata["LUNCH-1"]["sequence_state"] == "locked"

metadata = module._sequence_metadata(rows, {"BREAKFAST-1"}, datetime(2026, 9, 14, 5, 0, 0))
assert metadata["BREAKFAST-1"]["sequence_state"] == "completed"
assert metadata["BREAKFAST-2"]["sequence_state"] == "active"
assert metadata["LUNCH-1"]["sequence_state"] == "locked"

metadata = module._sequence_metadata(rows, {"BREAKFAST-1", "BREAKFAST-2"}, datetime(2026, 9, 14, 5, 0, 0))
assert metadata["LUNCH-1"]["sequence_state"] == "active"

metadata = module._sequence_metadata(rows, set(), datetime(2026, 9, 14, 9, 0, 0))
assert metadata["BREAKFAST-1"]["sequence_state"] == "missed"
assert metadata["BREAKFAST-2"]["sequence_state"] == "missed"
assert metadata["LUNCH-1"]["sequence_state"] == "active"
print("RC294 free hotel routing behaviour test passed")
