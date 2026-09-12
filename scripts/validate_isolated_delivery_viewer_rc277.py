#!/usr/bin/env python3
"""Static QA for the isolated RC277 delivery viewer shell."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


nav = read("wafd_one/public/js/wafd_mobile_navigation.js")
bundle = read("wafd_one/public/wafd_mobile_navigation.bundle.js")
viewer = read("wafd_one/wafd_one/page/wafd_delivery_viewer/wafd_delivery_viewer.js")
home = read("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js")

require(nav == bundle, "mobile navigation source and deployed bundle differ")
require('VIEWER_ROUTE = "wafd-delivery-viewer"' in nav, "viewer route isolation missing")
require("syncPwaChrome(home || driverTrips || cleaningHome || deliveryViewer)" in nav, "viewer Frappe chrome is not hidden")
require('id="wafv-language"' in viewer, "viewer language selector missing")
require("data-wafv-logout" in viewer, "viewer logout action missing")
require('method:"wafd_one.language.set_user_language"' in viewer, "viewer language persistence missing")
require('isolatedFieldRoles = new Set(["WAFD Driver", "WAFD Cleaning Supervisor", "WAFD Delivery Viewer"])' in home, "isolated field menu missing")
require("v10_0_0_rc277.execute" in read("wafd_one/patches.txt"), "RC277 patch missing")
require('version = "10.0.0rc' in read("pyproject.toml"), "release version missing")

print("RC277 isolated delivery viewer validation passed")
