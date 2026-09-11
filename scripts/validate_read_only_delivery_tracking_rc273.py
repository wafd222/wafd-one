#!/usr/bin/env python3
"""Static release checks for RC273 secure delivery tracking."""

from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


doctype = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_tracking_share/wafd_delivery_tracking_share.json"))
fields = {row["fieldname"]: row for row in doctype["fields"]}
for name in ("delivery_trip", "viewer_name", "expires_on", "enabled", "share_token", "access_count"):
    require(name in fields, f"missing share field: {name}")
require(fields["share_token"].get("unique") == 1 and fields["share_token"].get("hidden") == 1, "share token must be unique and hidden")
require(all(row["role"] != "Guest" for row in doctype["permissions"]), "Guest must not receive DocType permissions")

backend = read("wafd_one/delivery_tracking.py")
require("@frappe.whitelist(allow_guest=True)\ndef get_shared_tracking" in backend, "guest tracking endpoint missing")
require("@frappe.whitelist(allow_guest=True)\ndef get_shared_delivery_photo" in backend, "protected photo endpoint missing")
for guard in ('"enabled": 1', "expires_on", "attached_to_doctype", "attached_to_name"):
    require(guard in backend, f"security guard missing: {guard}")
for forbidden in ('cost_price', 'valuation_rate', 'latitude\":', 'longitude\":', 'notes\":', 'system_user\":'):
    require(forbidden not in backend, f"shared payload exposes forbidden data: {forbidden}")

trip = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json"))
require(any(row.get("fieldname") == "driver_accepted_on" and row.get("read_only") == 1 for row in trip["fields"]), "driver acceptance timestamp missing")
require("trip.driver_accepted_on = accepted_on" in read("wafd_one/driver_portal.py"), "driver start does not record acceptance")

page = read("wafd_one/www/wafd_delivery_tracking.html")
for label in ("اسم السائق", "رقم الجوال", "رقم اللوحة", "استلام السائق للمهمة", "وقت الخروج", "وقت الوصول", "اسم المستلم", "صورة إثبات التسليم", "للقراءة فقط"):
    require(label in page, f"public page label missing: {label}")
require("setInterval" in page and "30000" in page, "automatic refresh missing")
require("noindex" in page and "no-referrer" in page, "public-page privacy metadata missing")
require(not re.search(r"<(input|textarea|select)\b", page, re.I), "read-only page contains an editable control")

manager = read("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js")
require("data-share" in manager, "manager tracking action missing")
legacy_manager_flow = all(marker in manager for marker in ("create_tracking_share", "get_tracking_shares", "revoke_tracking_share"))
account_manager_flow = all(marker in manager for marker in ("assign_delivery_viewer", "get_trip_viewers", "remove_delivery_viewer"))
require(legacy_manager_flow or account_manager_flow, "manager tracking assignment flow missing")

patches = read("wafd_one/patches.txt")
require("v10_0_0_rc273.execute" in patches, "RC273 patch not registered")
version_match = re.search(r'version = "10\.0\.0rc(\d+)"', read("pyproject.toml"))
require(version_match and int(version_match.group(1)) >= 273, "release must retain the RC273 feature baseline")

print("RC273 read-only delivery tracking validation passed")
