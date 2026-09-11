#!/usr/bin/env python3
"""Static QA for RC275 beneficiary accounts and mobile date correction."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


employee = read("wafd_one/employee_team.py")
setup = read("wafd_one/setup.py")
tracking = read("wafd_one/delivery_tracking.py")
share = read("wafd_one/wafd_one/doctype/wafd_delivery_tracking_share/wafd_delivery_tracking_share.json")
supervisor = read("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js")
viewer = read("wafd_one/wafd_one/page/wafd_delivery_viewer/wafd_delivery_viewer.js")
viewer_page = read("wafd_one/wafd_one/page/wafd_delivery_viewer/wafd_delivery_viewer.json")
home = read("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js")

require('"WAFD Delivery Viewer": "متابعة بيانات التسليم"' in employee, "employee task label missing")
require('"WAFD Delivery Viewer"' in setup, "role setup missing")
require('"viewer_user"' in share, "beneficiary user link missing")
for endpoint in ("list_delivery_viewers", "assign_delivery_viewer", "get_trip_viewers", "remove_delivery_viewer", "get_my_delivery_tracking", "get_my_delivery_photo"):
    require(f"def {endpoint}" in tracking, f"{endpoint} missing")
require('viewer_user": frappe.session.user' in tracking, "viewer row-level restriction missing")
require('assign_delivery_viewer' in supervisor, "supervisor assignment workflow missing")
require('create_tracking_share' not in supervisor, "legacy public link creation remains visible")
require('.modal-dialog input[type=date]' in supervisor, "mobile date direction correction missing")
require('wafd-delivery-viewer' in viewer_page and 'WAFD Delivery Viewer' in viewer_page, "viewer page permission missing")
require('get_my_delivery_tracking' in viewer and 'get_my_delivery_photo' in viewer, "read-only viewer data/photo flow missing")
require('role: "WAFD Delivery Viewer"' in home, "viewer home card missing")
require("v10_0_0_rc275.execute" in read("wafd_one/patches.txt"), "RC275 patch missing")
require('version = "10.0.0rc275"' in read("pyproject.toml"), "RC275 version mismatch")

print("RC275 beneficiary account and mobile date validation passed")
