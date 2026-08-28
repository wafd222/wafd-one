"""Regression checks for RC244 driver identity aliases without a Frappe site."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True


class Row(dict):
    __getattr__ = dict.get


CURRENT_USER = "wafd.almadinah7@gmail.com"
ROWS = [
    Row(
        name="عمر - wafd.almadinah7",
        driver_name="عمر - wafd.almadinah7",
        system_user=CURRENT_USER,
        mobile="+966547726406",
        creation="2026-08-28 18:00:00",
    ),
    Row(
        name="عمر",
        driver_name="عمر",
        system_user=None,
        mobile="0547726406",
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
        name="عمر-آخر",
        driver_name="عمر آخر",
        system_user="other@example.com",
        mobile="0547726406",
        creation="2026-01-03 00:00:00",
    ),
]


class FakeDB:
    @staticmethod
    def escape(value):
        return "'" + str(value).replace("'", "''") + "'"

    @staticmethod
    def get_value(doctype, name, field):
        if doctype == "User" and field == "enabled":
            return 1
        if doctype == "WAFD Delivery Trip" and field == "driver":
            return "عمر"
        return None


fake_frappe = types.ModuleType("frappe")
fake_frappe.session = types.SimpleNamespace(user=CURRENT_USER)
fake_frappe.db = FakeDB()
fake_frappe.get_roles = lambda user=None: ["WAFD Driver"]
fake_frappe.get_all = lambda *args, **kwargs: ROWS

sys.modules["frappe"] = fake_frappe
module_path = Path(__file__).resolve().parents[1] / "wafd_one" / "driver_security.py"
spec = importlib.util.spec_from_file_location("rc244_driver_security", module_path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

drivers = module.get_drivers_for_user(CURRENT_USER)
assert drivers == ["عمر - wafd.almadinah7", "عمر"], drivers
assert "سالم" not in drivers
assert "عمر-آخر" not in drivers

trip_sql = module.delivery_trip_query(CURRENT_USER)
assert "عمر - wafd.almadinah7" in trip_sql and "عمر" in trip_sql
assert module.delivery_trip_has_permission(Row(driver="عمر"), CURRENT_USER)
assert not module.delivery_trip_has_permission(Row(driver="سالم"), CURRENT_USER)
assert module.delivery_proof_has_permission(Row(delivery_trip="TRIP-1"), CURRENT_USER)

resolved = module.resolve_linked_driver("عمر")
assert resolved == ("عمر - wafd.almadinah7", CURRENT_USER), resolved

print("RC244 driver identity validation passed")
