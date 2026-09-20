from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


portal = read("wafd_one/driver_portal.py")
standard = read("wafd_one/wafd_one/page/wafd_driver_trips/wafd_driver_trips.js")
iftar = read("wafd_one/wafd_one/page/wafd_iftar_driver/wafd_iftar_driver.js")
patch = read("wafd_one/wafd_one/patches/v10_0_0_rc337/execute.py")

assert portal.count('"already_synced": True') >= 4
sync_segment = portal.split("def sync_offline_driver_action", 1)[1]
assert sync_segment.index("existing_proof") < sync_segment.index('if action == "start"')

for page in (standard, iftar):
    assert "isAlreadySyncedError" in page
    assert "await deletePendingAction(row.id);\n            continue;" in page
    assert "const blockedTrips = new Set();" in page
    assert "if (blockedTrips.has(row.trip_name)) continue;" in page
    assert "const duplicate = (await pendingActions()).find" in page
    assert 'await updateOfflineBanner(hadValidationError ? "error" : "online")' in page

assert 'reload_doc("wafd_one", "page", "wafd_driver_trips"' in patch
assert 'reload_doc("wafd_one", "page", "wafd_iftar_driver"' in patch
assert "repair_trip_assignments()" in patch

print("RC337 driver trip visibility and offline sync checks passed")
