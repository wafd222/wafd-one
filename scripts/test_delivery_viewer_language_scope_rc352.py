"""Static regression checks for the isolated RC352 repair."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
viewer = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_viewer/wafd_delivery_viewer.js").read_text()
home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text()
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
employee = (ROOT / "wafd_one/employee_team.py").read_text()
setup = (ROOT / "wafd_one/setup.py").read_text()
patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc352/execute.py").read_text()

# Every language exposed by the selector has an explicit inner-screen catalog.
for language in ("id", "ur", "hi", "bn", "fr", "ha", "sw", "uz"):
    assert f"{language}:{{" in viewer, language
assert 'translations[lang]?.[e]' in viewer
assert 'localStorage.getItem("wafd_lang")' in viewer
assert 'const rtl = ["ar", "ur"].includes(lang)' in viewer
assert '"Delivery Data":"डिलीवरी डेटा"' in viewer
assert '"Delivery Data":"Data Pengiriman"' in viewer
for label in ("Customer", "Destination", "Meal", "Driver", "Receiver", "Delivered"):
    assert label in viewer

# Generic delivery and Iftar read-only access use distinct roles.
assert '"WAFD Delivery Viewer": "متابعة بيانات التسليم"' in employee
assert '"WAFD Iftar External Viewer": "متابع خارجي لإفطار الصائم"' in employee
assert 'EXTERNAL_VIEWER_ROLE = "WAFD Iftar External Viewer"' in portal
assert '"WAFD Iftar External Viewer"' in setup

# Iftar entry is added only after server-confirmed exact project assignment.
assert "has_my_external_viewer_assignment" in home
assert '"external_viewer_user": user' in portal
assert '"docstatus": 1' in portal
delivery_profile = home.split('role: "WAFD Delivery Viewer"', 1)[1].split('role: "WAFD Iftar External Viewer"', 1)[0]
assert 'page: "wafd-delivery-viewer"' in delivery_profile
assert 'page: "wafd-iftar-team"' not in delivery_profile

# Upgrade is additive and refreshes only the three affected pages.
assert "add_roles(IFTAR_VIEWER_ROLE)" in patch
for page in ("wafd_role_home", "wafd_delivery_viewer", "wafd_iftar_team"):
    assert page in patch
for forbidden in ("undertaking", "driver_trips", "delivery_supervisor", "production"):
    assert forbidden not in patch.lower()

print("RC352 delivery language and viewer-scope regression checks passed")
