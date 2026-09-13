#!/usr/bin/env python3
"""Static RC284 delivery equipment/report regression checks."""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


trip = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json"))
fields = {row["fieldname"]: row for row in trip["fields"]}
for name in ("contracting_entity", "safandash_count", "hot_cabinet_count"):
    assert name in fields, name
assert fields["safandash_count"]["label"].startswith("عدد السفندشات (اختياري)")
assert fields["hot_cabinet_count"]["label"].startswith("عدد السخانات Hot Cabinet (اختياري)")
assert fields["safandash_count"].get("non_negative") == 1
assert fields["hot_cabinet_count"].get("non_negative") == 1

supervisor = read("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js")
backend = read("wafd_one/delivery_supervisor.py")
report = read("wafd_one/delivery_report.py")
report_page = read("wafd_one/wafd_one/page/wafd_delivery_report/wafd_delivery_report.js")
home = read("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js")
dashboard = read("wafd_one/wafd_one/page/wafd_one_dashboard/wafd_one_dashboard.js")

for marker in ("contracting_entity", "safandash_count", "hot_cabinet_count"):
    assert marker in supervisor
    assert marker in backend
    assert marker in report
assert "destinationEquipment" in supervisor
assert "عدد السفندشات (اختياري)" in supervisor
assert "عدد السفندشات" in report
assert "الساندوتشات" not in supervisor + report
assert "السندوتشات" not in supervisor + report
for marker in ("كامل المدة", "حسب الشركة أو البعثة", "حسب الفندق", "تنزيل PDF", "مشاركة", "طباعة"):
    assert marker in report_page, marker
assert "MEAL DELIVERY EXECUTION REPORT" in report
assert "wafd-almadinah-official.png" in report
assert home.count('page: "wafd-delivery-report"') >= 3
assert 'data-route="wafd-delivery-report"' in dashboard
assert "v10_0_0_rc284.execute" in read("wafd_one/patches.txt")
assert 'version = "10.0.0rc284"' in read("pyproject.toml")

print("RC284 delivery report validation passed")
