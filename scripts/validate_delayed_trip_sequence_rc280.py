#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
portal = (root / "wafd_one/driver_portal.py").read_text(encoding="utf-8")
page = (root / "wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js").read_text(encoding="utf-8")
patches = (root / "wafd_one/patches.txt").read_text(encoding="utf-8")
version = (root / "pyproject.toml").read_text(encoding="utf-8")

assert '"start": ({"مخططة / Planned", "تم التحميل / Loaded", "متأخرة / Delayed"}' in portal
assert "if not trip.actual_departure:" in portal
assert "Start the trip before marking arrival" in portal
assert 'trip.status === "متأخرة / Delayed" && !trip.actual_departure' in page
assert 'trip.status === "متأخرة / Delayed" && trip.actual_departure' in page
assert "v10_0_0_rc280.execute" in patches
assert 'version = "10.0.0rc280"' in version
print("RC280 delayed trip sequence validation passed")
