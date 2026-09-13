"""Static validation for the RC289 delivery supervisor shell correction."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
navigation = (ROOT / "wafd_one/public/js/wafd_mobile_navigation.js").read_text(encoding="utf-8")
bundle = (ROOT / "wafd_one/public/wafd_mobile_navigation.bundle.js").read_text(encoding="utf-8")

assert 'DELIVERY_SUPERVISOR_ROUTE = "wafd-delivery-supervisor"' in navigation
assert "function isDeliverySupervisorPage()" in navigation
assert "(deliveryReport || deliverySupervisorPage) && isDeliverySupervisorShell()" in navigation
assert "roles.has(\"WAFD Delivery Supervisor\")" in navigation
assert "!roles.has(\"System Manager\")" in navigation
assert "!roles.has(\"WAFD Operations Manager\")" in navigation
assert "syncPwaChrome(home || driverTrips || cleaningHome || deliveryViewer || deliverySupervisorShell)" in navigation
assert "syncFieldAppbar(driverTrips || cleaningHome || deliverySupervisorShell)" in navigation
assert navigation == bundle
print("RC289 delivery supervisor mobile shell checks passed")
