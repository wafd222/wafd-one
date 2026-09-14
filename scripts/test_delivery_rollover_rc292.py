"""Behaviour tests for RC292 driver rollover and supervisor log transfer."""

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
frappe.get_all = lambda *args, **kwargs: []
frappe.get_doc = lambda *args, **kwargs: None
frappe.throw = lambda message, *args: (_ for _ in ()).throw(RuntimeError(message))
frappe.db = SimpleNamespace(get_value=lambda *args, **kwargs: None, exists=lambda *args, **kwargs: False)

utils = ModuleType("frappe.utils")
utils.cint = lambda value: int(value or 0)
utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
utils.now_datetime = lambda: datetime(2026, 9, 13, 12, 0, 0)
utils.nowdate = lambda: "2026-09-13"
utils.getdate = lambda value=None: datetime.fromisoformat(str(value or "2026-09-13")).date()
utils.add_days = lambda value, days: value
sys.modules["frappe"] = frappe
sys.modules["frappe.utils"] = utils

security = ModuleType("wafd_one.driver_security")
security.get_drivers_for_user = lambda user: ["DRIVER-1"]
security.repair_trip_assignments = lambda user: None
security.trip_is_assigned_to_user = lambda *args: True
security.trips_for_user = lambda trips, user: trips
sys.modules["wafd_one.driver_security"] = security

employee = ModuleType("wafd_one.employee_team")
employee._normalize_mobile = lambda value, required=False: value
sys.modules["wafd_one.employee_team"] = employee

reconciliation = ModuleType("wafd_one.delivery_reconciliation")
reconciliation.reconcile_missing_delivery_trips = lambda **kwargs: {"counts": {}, "results": []}
sys.modules["wafd_one.delivery_reconciliation"] = reconciliation

root = Path(__file__).resolve().parents[1]


def load(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, root / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


driver = load("driver_portal_rc292_test", "wafd_one/driver_portal.py")
supervisor = load("delivery_supervisor_rc292_test", "wafd_one/delivery_supervisor.py")

trips = [
    SimpleNamespace(name="DONE-YESTERDAY", planned_arrival=datetime(2026, 9, 12, 4, 0)),
    SimpleNamespace(name="MISSED-YESTERDAY", planned_arrival=datetime(2026, 9, 12, 10, 0)),
    SimpleNamespace(name="DONE-TODAY", planned_arrival=datetime(2026, 9, 13, 4, 0)),
    SimpleNamespace(name="NEXT-DAY", planned_arrival=datetime(2026, 9, 14, 4, 0)),
    SimpleNamespace(name="LATER-NEXT-DAY", planned_arrival=datetime(2026, 9, 14, 10, 0)),
]
proofs = {"DONE-YESTERDAY", "DONE-TODAY"}
states = driver._sequence_metadata(trips, proofs, datetime(2026, 9, 13, 12, 0))

assert states["DONE-YESTERDAY"]["sequence_state"] == "completed"
assert states["DONE-TODAY"]["sequence_state"] == "completed"
assert states["MISSED-YESTERDAY"]["sequence_state"] == "missed"
assert states["MISSED-YESTERDAY"]["sequence_actionable"] is True
assert states["NEXT-DAY"]["sequence_state"] == "active"
assert states["LATER-NEXT-DAY"]["sequence_state"] == "locked"

board_rows = [
    {"name": "DONE-YESTERDAY", "proof": {"name": "PROOF-1"}},
    {"name": "MISSED-YESTERDAY", "proof": None},
    {"name": "DONE-TODAY", "proof": {"name": "PROOF-2"}},
    {"name": "NEXT-DAY", "proof": None},
]
current, delivered = supervisor._split_delivery_board(board_rows)
assert [row["name"] for row in current] == ["MISSED-YESTERDAY", "NEXT-DAY"]
assert [row["name"] for row in delivered] == ["DONE-YESTERDAY", "DONE-TODAY"]
print("RC292 delivery rollover behaviour test passed")
