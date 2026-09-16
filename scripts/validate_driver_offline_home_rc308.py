"""Static release checks for RC308 driver offline-first home and reconnect sync."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path, needles):
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")


require("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js", [
    'const DRIVER_OFFLINE_DB_NAME = "wafd_driver_offline_rc293"',
    "preloadDriverOfflineData",
    "driverPendingActions",
    'method:"wafd_one.driver_portal.sync_offline_driver_action"',
    'method:"wafd_one.driver_portal.list_my_trips"',
    'id="wafd-driver-connectivity"',
    'window.addEventListener("offline"',
    'window.addEventListener("online"',
    'wrapper.wafdPreloadDriverOffline = preloadDriverOfflineData',
])
require("wafd_one/public/js/wafd_driver_offline_guard.js", [
    "NETWORK_TEXT",
    "WAFD Driver",
    'patch("show_alert")',
    'patch("msgprint")',
    "MutationObserver",
    'new CustomEvent("wafd-driver-connectivity"',
])
require("wafd_one/hooks.py", [
    '"/assets/wafd_one/js/wafd_driver_offline_guard.js"',
])
require("wafd_one/wafd_one/patches/v10_0_0_rc308/execute.py", [
    '"wafd_role_home", "wafd_driver_trips"',
    "frappe.clear_cache()",
])
require("wafd_one/patches.txt", [
    "wafd_one.wafd_one.patches.v10_0_0_rc308.execute",
])
print("RC308 driver offline-first home checks passed")
