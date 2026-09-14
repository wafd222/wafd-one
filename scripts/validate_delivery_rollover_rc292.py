"""Static release checks for RC292 automatic delivery rollover."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path, needles):
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")


require("wafd_one/driver_portal.py", [
    "DRIVER_QUEUE_LIMIT = 10000",
    "limit_page_length=DRIVER_QUEUE_LIMIT",
    'state in {"missed", "active"}',
])
require("wafd_one/delivery_supervisor.py", [
    "DELIVERY_BOARD_LIMIT = 10000",
    "def _split_delivery_board(trips):",
    'delivered if row.get("proof") else current',
])
require("wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js", [
    "await loadTrips();",
])
require("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js", [
    'data-view="current"', 'data-view="delivered"',
])
print("RC292 delivery rollover checks passed")
