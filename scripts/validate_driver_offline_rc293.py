"""Static release checks for RC293 driver offline delivery."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path, needles):
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")


require("wafd_one/driver_portal.py", [
    "OFFLINE_PRELOAD_COUNT = 100", "def _validated_offline_time(value):",
    "def sync_offline_driver_action", 'action not in {"start", "arrive", "proof"}',
    '"sequence_visible": is_manager or trip.name in rendered',
])
require("wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js", [
    'const OFFLINE_DB_NAME = "wafd_driver_offline_rc293"', "window.indexedDB",
    "queueOfflineAction", "syncPendingActions", "saved_offline", "wafd-sync-now",
    'window.addEventListener("offline"', 'window.addEventListener("online"',
    'method:"wafd_one.driver_portal.sync_offline_driver_action"',
])
require("wafd_one/wafd_one/patches/v10_0_0_rc293/execute.py", [
    'frappe.reload_doc("wafd_one", "page", "wafd_driver_trips", force=True)',
])
print("RC293 driver offline delivery checks passed")
