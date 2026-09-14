"""Static checks for RC294 free routing inside one driver meal run."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path, needles):
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")


require("wafd_one/driver_portal.py", [
    "Sequence meal runs while allowing destinations in one run in any order",
    "def run_key(trip):", '"sequence_run_index": run_index',
    'state = "locked" if blocking_run else ("missed" if overdue else "active")',
    '"vehicle",', '"meal_type", "assigned_driver_user"',
])
require("wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js", [
    "current_round", "فنادق الجولة الحالية", "const runKey = trip =>",
    'const state = activeAssigned ? "locked" : (overdue ? "missed" : "active")',
])
print("RC294 free hotel routing checks passed")
