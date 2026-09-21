"""Static regression checks for the RC344 Iftar-only role entry fix."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text()
team = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text()
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()

assert 'iftar_mode: "kitchen"' in home
assert 'iftar_mode: "delivery"' in home
assert 'iftar_mode: "project_manager"' in home
assert 'sessionStorage.setItem("wafd_iftar_requested_mode"' in home
assert 'call("get_portal_data", {requested_mode})' in team
assert "def get_portal_data(requested_mode=None):" in portal
assert 'requested_mode in {"project_manager", "kitchen", "delivery", "viewer"}' in portal
assert 'إسناد شاشات مشروع إفطار الصائم' not in team
assert 'ift-assign-team' not in team
assert 'إدارة الموظفين والمهمات' in team
assert '<b>مشرفو السفر</b>' in team

# This release must remain isolated from undertaking and generic delivery code.
for forbidden in (
    "wafd_one/undertaking_security.py",
    "wafd_one/undertaking_file_security.py",
    "wafd_one/delivery_tracking.py",
    "wafd_one/driver_portal.py",
):
    assert forbidden not in (ROOT / "RELEASE_NOTES_10.0.0rc344.md").read_text()

print("RC344 Iftar isolation and explicit multi-role entry checks passed")
