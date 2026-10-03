"""Static regression checks for RC352 Iftar viewer card visibility."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text()

assert "def has_iftar_viewer_access():" in portal
assert '"external_viewer_user": user' in portal
assert '"docstatus": 1' in portal
assert '"status": ["not in", ["ملغي / Cancelled"]]' in portal
assert "start_date" in portal and "end_date" in portal
assert 'roles.has("WAFD Delivery Viewer")' in home
assert "has_iftar_viewer_access" in home
assert 'items = items.filter((item) => item.iftar_mode !== "viewer")' in home
assert "Fail closed" in home
assert "No project-scoped Iftar tracking assignment" in portal
assert "EXTERNAL_VIEWER_ROLE in roles" in portal

print("RC352 Iftar viewer assignment visibility checks passed")
