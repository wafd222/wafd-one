"""Static checks for the RC296 storekeeper and delivery-board improvements."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

api = (ROOT / "wafd_one/api.py").read_text(encoding="utf-8")
storekeeper = (ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home/wafd_storekeeper_home.js").read_text(encoding="utf-8")
storekeeper_css = (ROOT / "wafd_one/wafd_one/page/wafd_storekeeper_home/wafd_storekeeper_home.css").read_text(encoding="utf-8")
delivery = (ROOT / "wafd_one/delivery_supervisor.py").read_text(encoding="utf-8")
delivery_page = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js").read_text(encoding="utf-8")
patches = (ROOT / "wafd_one/patches.txt").read_text(encoding="utf-8")

assert 'bootinfo.home_page = "wafd-storekeeper-home"' in api
assert "refreshReceiptMaterials" in storekeeper
assert 'id="wafd-receipt-category"' not in storekeeper[storekeeper.index("async function openReceipt"):storekeeper.index("async function openHandover")]
assert "overflow-x:hidden" in storekeeper_css
assert "grid-template-columns:28px minmax(0,1fr)" in storekeeper_css
assert "def _group_delivery_board" in delivery
for bucket in ("planned", "in_transit", "attention", "delivered"):
    assert f'"{bucket}"' in delivery
    assert f'key:"{bucket}"' in delivery_page
assert 'tr("عدد السفندشات","Safandash")' in delivery_page
assert 'tr("عدد السخانات Hot Cabinet","Hot Cabinets")' in delivery_page
assert "wafd_one.wafd_one.patches.v10_0_0_rc296.execute" in patches

print("RC296 storekeeper and delivery-board checks passed")
