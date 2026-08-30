"""Regression checks for RC247 approved-loading trip reconciliation."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


CURRENT_USER = "driver@example.com"
OTHER_USER = "other@example.com"
LOADINGS = [
    Row(name="LOAD-1", project="P1", meal_plan="M1", loading_date="2026-08-30 08:00:00", quantity=50, vehicle="V1", driver="DRIVER-1", supervisor="manager@example.com", loading_photo="/private/files/load1.jpg", hotel="H1", status="تم التحميل / Loaded", creation="1"),
    Row(name="LOAD-2", project="P1", meal_plan="M1", loading_date="2026-08-30 09:00:00", quantity=40, vehicle="V2", driver="LEGACY-1", supervisor="manager@example.com", loading_photo="/private/files/load2.jpg", hotel="H1", status="تم التحميل / Loaded", creation="2"),
    Row(name="LOAD-3", project="P1", meal_plan="M1", loading_date="2026-08-30 10:00:00", quantity=30, vehicle="V3", driver="DRIVER-1", supervisor="manager@example.com", loading_photo="", hotel="H1", status="تم التحميل / Loaded", creation="3"),
    Row(name="LOAD-4", project="P2", meal_plan="M2", loading_date="2026-08-30 11:00:00", quantity=20, vehicle="V4", driver="DRIVER-2", supervisor="manager@example.com", loading_photo="/private/files/load4.jpg", hotel="H2", status="خرجت / Dispatched", creation="4"),
]
TRIPS = {
    "LOAD-2": Row(name="TRIP-2", driver="LEGACY-1", assigned_driver_user="disabled@example.com", status="تم التحميل / Loaded"),
}


def get_all(doctype, filters=None, fields=None, order_by=None, **kwargs):
    if doctype != "WAFD Loading Record":
        return []
    rows = LOADINGS
    driver_filter = (filters or {}).get("driver")
    if driver_filter:
        allowed = set(driver_filter[1])
        rows = [row for row in rows if row.driver in allowed]
    return rows


class FakeDB:
    @staticmethod
    def get_value(doctype, filters, fields, as_dict=False):
        if doctype == "WAFD Delivery Trip":
            row = TRIPS.get(filters["loading_record"])
            return row if as_dict else (row.name if row else None)
        if doctype == "WAFD Meal Plan" and fields == "service_date":
            return "2026-08-30"
        return None

    @staticmethod
    def set_value(doctype, name, field, value=None, update_modified=False):
        if doctype == "WAFD Loading Record":
            row = next(item for item in LOADINGS if item.name == name)
            row[field] = value
            return
        assert doctype == "WAFD Delivery Trip"
        row = next(item for item in TRIPS.values() if item.name == name)
        if isinstance(field, dict):
            row.update(field)
        else:
            row[field] = value


class FakeTrip(Row):
    def insert(self, ignore_permissions=False):
        assert ignore_permissions
        self.name = f"TRIP-{len(TRIPS) + 1}"
        TRIPS[self.loading_record] = Row(
            name=self.name,
            driver=self.driver,
            assigned_driver_user=self.assigned_driver_user,
            status=self.status,
        )


fake_frappe = types.ModuleType("frappe")
fake_frappe.session = types.SimpleNamespace(user=CURRENT_USER)
fake_frappe.get_all = get_all
fake_frappe.db = FakeDB()
fake_frappe.get_doc = lambda values: FakeTrip(values)
fake_frappe_utils = types.ModuleType("frappe.utils")
fake_frappe_utils.cint = lambda value: int(value or 0)
fake_frappe_utils.getdate = lambda value: str(value).split()[0]
fake_frappe_utils.nowdate = lambda: "2026-08-30"

security = types.ModuleType("wafd_one.driver_security")
security.get_drivers_for_user = lambda user: ["DRIVER-1", "LEGACY-1"] if user == CURRENT_USER else ["DRIVER-2"]
security.resolve_linked_driver = lambda driver: {
    "DRIVER-1": ("DRIVER-1", CURRENT_USER),
    "LEGACY-1": ("DRIVER-1", CURRENT_USER),
    "DRIVER-2": ("DRIVER-2", OTHER_USER),
}.get(driver, (None, None))

sys.modules["frappe"] = fake_frappe
sys.modules["frappe.utils"] = fake_frappe_utils
sys.modules["wafd_one.driver_security"] = security

module_path = Path(__file__).resolve().parents[1] / "wafd_one/delivery_reconciliation.py"
spec = importlib.util.spec_from_file_location("rc247_delivery_reconciliation", module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

first = module.reconcile_missing_delivery_trips(user=CURRENT_USER)
assert first["counts"] == {"created": 1, "repaired": 1, "existing": 0, "blocked": 1}, first
assert TRIPS["LOAD-1"].assigned_driver_user == CURRENT_USER
assert TRIPS["LOAD-2"].driver == "DRIVER-1"
assert TRIPS["LOAD-2"].assigned_driver_user == CURRENT_USER
assert "LOAD-4" not in TRIPS, "another driver's loading leaked into the scoped repair"

second = module.reconcile_missing_delivery_trips(user=CURRENT_USER)
assert second["counts"] == {"created": 0, "repaired": 0, "existing": 2, "blocked": 1}, second

all_rows = module.reconcile_missing_delivery_trips(all_drivers=True)
assert all_rows["counts"]["created"] == 1, all_rows
assert TRIPS["LOAD-4"].assigned_driver_user == OTHER_USER

print("RC247 approved-loading delivery reconciliation validation passed")
