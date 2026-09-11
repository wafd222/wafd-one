#!/usr/bin/env python3
"""Static QA for RC276 Iftar contract/delivery integration."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


trip = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json"))
trip_fields = {field.get("fieldname") for field in trip.get("fields", [])}
iftar = json.loads(read("wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json"))
iftar_fields = {field.get("fieldname") for field in iftar.get("fields", [])}
backend = read("wafd_one/delivery_supervisor.py")
iftar_backend = read("wafd_one/wafd_one/iftar_pro.py")
supervisor = read("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js")
operations = read("wafd_one/wafd_one/page/wafd_iftar_operations/wafd_iftar_operations.js")
manager = read("wafd_one/wafd_one/page/wafd_one_dashboard/wafd_one_dashboard.js")
executive = read("wafd_one/executive.py")

require({"contract", "iftar_project", "iftar_daily_operation", "iftar_link_type"} <= trip_fields, "trip bridge fields missing")
require({"contract", "catering_project"} <= iftar_fields, "Iftar project bridge fields missing")
require("def create_iftar_delivery_task" in backend, "dedicated Iftar delivery endpoint missing")
require("مرتبط بعقد / Contract Linked" in backend and "بدون عقد / No Contract" in backend, "delivery classification missing")
require("عدد وجبات إفطار صائم يجب أن يكون أكبر من صفر" in backend, "positive Iftar quantity validation missing")
require("get_iftar_contract_context" in iftar_backend, "Iftar wizard contract context missing")
require("إرسال إفطار صائم" in supervisor and "بدون عقد" in supervisor, "supervisor contract/standalone UI missing")
require("عمليات التوصيل" in operations and "توثيق السائق" in operations, "Iftar evidence view missing")
require("wafd-iftar-summary" in manager and "iftar_snapshot" in executive, "manager Iftar summary missing")
require("v10_0_0_rc276.execute" in read("wafd_one/patches.txt"), "RC276 patch missing")
require('version = "10.0.0rc276"' in read("pyproject.toml"), "RC276 version mismatch")

print("RC276 Iftar contract/delivery bridge validation passed")
