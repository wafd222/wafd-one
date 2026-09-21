"""Regression checks for RC348 Iftar trips without generic loading records."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
controller = (ROOT / "wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.py").read_text()
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc348/execute.py").read_text()
meta = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json").read_text())

source = "خطة تحميل إفطار الصائم / Iftar Loading Plan"
trip_source = next(field for field in meta["fields"] if field.get("fieldname") == "trip_source")
assert source in trip_source["options"].splitlines()
assert f'IFTAR_LOADING_PLAN = "{source}"' in controller

validate = controller.split("def validate(self):", 1)[1].split("def after_insert", 1)[0]
assert "iftar_plan = self.trip_source == IFTAR_LOADING_PLAN or bool(self.iftar_daily_operation)" in validate
assert "if iftar_plan:" in validate
assert "self._validate_iftar_plan()" in validate

iftar_validator = controller.split("def _validate_iftar_plan(self):", 1)[1].split("def _fill_planned_times", 1)[0]
assert "self.loading_record = None" in iftar_validator
assert '"WAFD Iftar Daily Operation"' in iftar_validator
assert "operation.project != self.iftar_project" in iftar_validator
assert "self._validate_supervisor_plan()" in iftar_validator
assert "_validate_loading_trip" not in iftar_validator
assert "_validate_food_safety_release" not in iftar_validator

assert f'"trip_source": "{source}"' in portal
assert 'frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)' in patch

print("RC348 isolated Iftar loading-plan trip validation checks passed")
