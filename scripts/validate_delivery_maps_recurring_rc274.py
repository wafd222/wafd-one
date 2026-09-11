#!/usr/bin/env python3
"""Static QA for RC274 delivery maps, editing and recurring schedules."""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


driver_backend = read("wafd_one/driver_portal.py")
driver_page = read("wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js")
supervisor_backend = read("wafd_one/delivery_supervisor.py")
supervisor_page = read("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js")
trip_meta = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json"))

for marker in ("quote_plus(destination_label)", "google.com/maps/search", '"map_url": trip.destination_map_url'):
    require(marker in driver_backend, f"driver map fallback missing: {marker}")
for marker in ("placeMapByDestination", "wafd-map-by-name", 'tr("open_map")'):
    require(marker in driver_page, f"map beside destination missing: {marker}")

for method in ("search_delivery_destinations", "update_delivery_destination", "remove_delivery_destination", "update_planned_trip", "archive_delivery_trip", "create_recurring_delivery_tasks"):
    require(f"def {method}(" in supervisor_backend, f"supervisor endpoint missing: {method}")
require("days > 90" in supervisor_backend, "90-day schedule limit missing")
require("skipped_duplicates" in supervisor_backend and "frappe.db.exists(\"WAFD Delivery Trip\", duplicate_filters)" in supervisor_backend, "duplicate prevention missing")
require("غير نشط / Inactive" in supervisor_backend, "safe destination removal missing")
require("frappe.delete_doc" not in supervisor_backend, "destination history must not be hard deleted")
require("An active driver trip cannot be removed before completion" in supervisor_backend, "active-trip deletion guard missing")

for marker in ("openRecurring", "openEditTrip", "wafd-destination-manager", "data-archive-trip", "data-dm-remove"):
    require(marker in supervisor_page, f"supervisor UI missing: {marker}")
for label in ("جدولة عدة أيام", "تعديل الطلب", "حذف الطلب", "إدارة المواقع والفنادق"):
    require(label in supervisor_page, f"Arabic supervisor label missing: {label}")

fields = {row.get("fieldname"): row for row in trip_meta["fields"]}
for name in ("archived_from_board", "archived_on", "archived_by"):
    require(name in fields and fields[name].get("read_only") == 1, f"safe archive field missing: {name}")

require("v10_0_0_rc274.execute" in read("wafd_one/patches.txt"), "RC274 patch missing")
require('version = "10.0.0rc274"' in read("pyproject.toml"), "RC274 version mismatch")
print("RC274 delivery map and recurring schedule validation passed")

