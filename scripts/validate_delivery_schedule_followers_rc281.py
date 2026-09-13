"""Static release checks for RC281 customer schedule followers."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
trip_json = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json").read_text())
fields = {row["fieldname"] for row in trip_json["fields"]}
assert {"delivery_schedule_id", "schedule_customer"} <= fields

tracking = (ROOT / "wafd_one/delivery_tracking.py").read_text()
assert "def assign_schedule_viewers" in tracking
assert "def inherit_schedule_viewers" in tracking
assert 'MANAGER_ROLES = {"System Manager", "WAFD Operations Manager"}' in tracking

supervisor = (ROOT / "wafd_one/delivery_supervisor.py").read_text()
assert "customer_name=None, viewers=None" in supervisor
assert '"delivery_schedule_id": schedule_id' in supervisor
assert "assign_schedule_viewers(created, viewer_users)" in supervisor

ui = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js").read_text()
assert "selectedDestinations=new Set(),selectedViewers=new Set()" in ui
assert "data.viewer_scope" in ui
assert "متابعو الجدول" in ui

assert 'version = "10.0.0rc281"' in (ROOT / "pyproject.toml").read_text()
print("RC281 customer schedule follower validation passed")
