"""Static validation for RC297 delivery status filters and optional quantities."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
supervisor = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_supervisor/wafd_delivery_supervisor.js").read_text(encoding="utf-8")
viewer = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_viewer/wafd_delivery_viewer.js").read_text(encoding="utf-8")
tracking = (ROOT / "wafd_one/delivery_tracking.py").read_text(encoding="utf-8")
supervisor_api = (ROOT / "wafd_one/delivery_supervisor.py").read_text(encoding="utf-8")
patches = (ROOT / "wafd_one/patches.txt").read_text(encoding="utf-8")

# Only the lower interactive queue controls remain on the supervisor page.
assert "queueCards" not in supervisor
assert '<section class="wafd-delivery-summary">' not in supervisor
assert 'data-view="${queue.key}"' in supervisor

# The read-only viewer uses the same four queue filters and receives their counts.
for bucket in ("in_transit", "planned", "attention", "delivered"):
    assert f'key:"{bucket}"' in viewer
assert "data-wafv-view" in viewer
assert "def _tracking_bucket" in tracking
assert 'trip["board_bucket"] = _tracking_bucket(trip)' in tracking
assert '"summary": summary' in tracking

# Optional numeric cards render only for positive values.
assert "Number(value) > 0" in viewer
assert 'row.safandash_count' in viewer and 'row.hot_cabinet_count' in viewer
assert '"safandash_count", "hot_cabinet_count"' in tracking
assert "عدد وجبات إفطار صائم يجب أن يكون أكبر من صفر" not in supervisor_api
assert '#v-qty,#v-saf,#v-hot' in supervisor
assert '#vi-qty,#vi-saf,#vi-hot' in supervisor
assert "wafd_one.wafd_one.patches.v10_0_0_rc297.execute" in patches

print("RC297 delivery viewer filters and optional-count checks passed")
