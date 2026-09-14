"""Static validation for the RC291 shared vehicle meal-run departure."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
portal = (ROOT / "wafd_one/driver_portal.py").read_text(encoding="utf-8")

required = [
    "def _same_delivery_run_rows(trip):",
    '"trip_date": trip.trip_date',
    '"driver": trip.driver',
    '"meal_type": trip.meal_type',
    'filters["vehicle"] = trip.vehicle if trip.vehicle else ["is", "not set"]',
    "departure_time = min(existing_times) if existing_times else now_datetime()",
    "def _start_delivery_run(trip):",
    '"driver_accepted_on": departure_time',
    '"actual_departure": departure_time',
    '"status": "في الطريق / In Transit"',
    '"delay_minutes": delay_minutes',
    '"status": "خرجت / Dispatched", "dispatch_time": departure_time',
    "departure_time, updated_names = _start_delivery_run(trip)",
    '"started_count": len(updated_names)',
]
missing = [item for item in required if item not in portal]
if missing:
    raise AssertionError(f"driver_portal.py missing RC291 safeguards: {missing}")
print("RC291 shared vehicle meal-run departure checks passed")
