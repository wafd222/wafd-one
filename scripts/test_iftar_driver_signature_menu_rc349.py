#!/usr/bin/env python3
"""Static regression checks for the isolated RC349 mobile fixes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRIVER = (ROOT / "wafd_one" / "driver_portal.py").read_text(encoding="utf-8")
NAV = (ROOT / "wafd_one" / "public" / "wafd_mobile_navigation.bundle.js").read_text(encoding="utf-8")
IFTAR_DRIVER = (ROOT / "wafd_one" / "wafd_one" / "page" / "wafd_iftar_driver" / "wafd_iftar_driver.js").read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


require(
    DRIVER.count('simple_delivery = trip.trip_source == "خطة مشرف التوصيل / Delivery Supervisor Plan"') == 1,
    "server delivery-proof validation must simplify only the generic supervisor plan",
)
require(
    DRIVER.count('"simple_delivery": trip.trip_source == "خطة مشرف التوصيل / Delivery Supervisor Plan"') == 1,
    "trip payload must expose the same simple-delivery rule",
)
require(
    '"خطة تحميل إفطار الصائم / Iftar Loading Plan"' not in "\n".join(
        line for line in DRIVER.splitlines() if "simple_delivery" in line
    ),
    "Iftar loading trips must never hide receiver signature as simple delivery",
)
require('id="wafd-signature"' in IFTAR_DRIVER and "setupSignature()" in IFTAR_DRIVER, "Iftar driver signature canvas is missing")
require('const IFTAR_DRIVER_ROUTE = "wafd-iftar-driver";' in NAV, "Iftar driver route is not allowed for field users")
require('routeName.startsWith("wafd-iftar-")' in NAV, "dedicated Iftar route detection is missing")
require("iftarAppRoute" in NAV and "syncFieldAppbar" in NAV, "compact Iftar app menu is not wired")
for required in ("data-wafd-field-home", "wafd-field-language", "data-wafd-field-logout"):
    require(required in NAV, f"compact menu item missing: {required}")

print("RC349 Iftar driver signature/menu regression checks passed")
