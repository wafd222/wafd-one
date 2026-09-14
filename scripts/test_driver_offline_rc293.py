"""Behaviour checks for RC293 offline timestamps and retry idempotency."""

from datetime import datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
import importlib.util
import sys


trip = SimpleNamespace(
    name="TRIP-1", driver="DRIVER-1", assigned_driver_user="driver@example.com",
    status="مخططة / Planned", actual_departure=None, actual_arrival=None,
    trip_source="خطة مشرف التوصيل / Delivery Supervisor Plan",
)
trip.check_permission = lambda permission: None

frappe = ModuleType("frappe")
frappe.session = SimpleNamespace(user="driver@example.com")
frappe.PermissionError = PermissionError
frappe._ = lambda value: value
frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn) if not args else args[0]
frappe.get_roles = lambda user=None: ["WAFD Driver"]
frappe.get_doc = lambda doctype, name: trip
frappe.get_all = lambda *args, **kwargs: []
frappe.throw = lambda message, *args: (_ for _ in ()).throw(RuntimeError(message))
frappe.parse_json = lambda value: value
frappe.db = SimpleNamespace(
    get_value=lambda doctype, filters, field, **kwargs: "PROOF-1" if doctype == "WAFD Delivery Proof" else None,
    exists=lambda *args, **kwargs: False,
)

utils = ModuleType("frappe.utils")
utils.cint = lambda value: int(value or 0)
utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
utils.now_datetime = lambda: datetime(2026, 9, 14, 12, 0, 0)
sys.modules["frappe"] = frappe
sys.modules["frappe.utils"] = utils

security = ModuleType("wafd_one.driver_security")
security.get_drivers_for_user = lambda user: ["DRIVER-1"]
security.repair_trip_assignments = lambda user: None
security.trip_is_assigned_to_user = lambda driver, assigned, user: assigned == user
security.trips_for_user = lambda rows, user: rows
sys.modules["wafd_one.driver_security"] = security

employee = ModuleType("wafd_one.employee_team")
employee._normalize_mobile = lambda value, required=False: value
sys.modules["wafd_one.employee_team"] = employee

reconciliation = ModuleType("wafd_one.delivery_reconciliation")
reconciliation.reconcile_missing_delivery_trips = lambda **kwargs: {"counts": {}, "results": []}
sys.modules["wafd_one.delivery_reconciliation"] = reconciliation

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("driver_portal_rc293_test", root / "wafd_one/driver_portal.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

captured = module._validated_offline_time("2026-09-14 09:30:00")
assert captured == datetime(2026, 9, 14, 9, 30, 0)

try:
    module._validated_offline_time("2026-09-14 12:30:00")
except RuntimeError as error:
    assert "المستقبل" in str(error)
else:
    raise AssertionError("Future device timestamps must be rejected")

# A proof retry after the server committed must return the original proof even
# if the response was lost and the cached trip still says Planned.
result = module.submit_delivery_proof("TRIP-1", image_data="cached-image")
assert result == {"name": "PROOF-1", "created": False}

trip.actual_departure = datetime(2026, 9, 14, 8, 0, 0)
result = module.sync_offline_driver_action("TRIP-1", "start", "2026-09-14 08:00:00")
assert result["already_synced"] is True
print("RC293 offline driver behaviour test passed")
