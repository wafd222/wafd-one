"""Static release checks for RC287 delivery sequencing and management."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path, needles):
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")


require("wafd_one/driver_portal.py", [
    "SEQUENCE_GRACE_HOURS = 2", "_assert_sequence_actionable(trip)",
    '"missed" if overdue else "active"', '"hidden_upcoming_count"',
])
require("wafd_one/delivery_supervisor.py", [
    "def update_delivery_schedule", "def archive_delivery_schedule",
    "_management_audit", "proof_preserved",
])
require("wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js", [
    "missed_delivery", "locked_delivery", "wafdSequenceTimer",
])
require("wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js", [
    "data-edit-schedule", "data-archive-schedule", "change_reason",
])
print("RC287 sequential delivery checks passed")
