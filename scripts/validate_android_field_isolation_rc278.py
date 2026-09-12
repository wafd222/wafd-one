#!/usr/bin/env python3
"""Static QA for RC278 Android field-role routing and shell isolation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


nav = read("wafd_one/public/js/wafd_mobile_navigation.js")
bundle = read("wafd_one/public/wafd_mobile_navigation.bundle.js")
css = read("wafd_one/public/css/wafd_mobile_navigation.css")
css_bundle = read("wafd_one/public/wafd_mobile_navigation.bundle.css")
home = read("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js")
api = read("wafd_one/api.py")
hooks = read("wafd_one/hooks.py")

require(nav == bundle, "mobile navigation source and deployed bundle differ")
require(css == css_bundle, "mobile navigation CSS source and deployed bundle differ")
for route in ("wafd-driver-trips", "wafd-cleaning-home", "wafd-delivery-viewer"):
    require(route in nav, f"isolated route missing: {route}")
require("function enforceFieldHome()" in nav, "field route guard missing")
require('window.location.replace("/app/wafd-role-home")' in nav, "direct canonical redirect missing")
require("syncPwaChrome(home || driverTrips || cleaningHome || deliveryViewer)" in nav, "internal field chrome isolation missing")
require("syncFieldAppbar(driverTrips || cleaningHome)" in nav, "driver/cleaning compact appbar missing")
require("data-wafd-field-logout" in nav and "wafd-field-language" in nav, "field menu is not limited to language/logout")
require("isolatedFieldProfile" in home, "multi-field role-home isolation missing")
require('bootinfo.home_page = "wafd-role-home"' in api, "server boot home missing")
require('boot_session = "wafd_one.api.boot_session"' in hooks, "boot session hook missing")
require("v10_0_0_rc278.execute" in read("wafd_one/patches.txt"), "RC278 patch missing")
require('version = "10.0.0rc' in read("pyproject.toml"), "release version missing")

print("RC278 Android field isolation validation passed")
