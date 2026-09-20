from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
security = (ROOT / "wafd_one/undertaking_security.py").read_text()
file_security = (ROOT / "wafd_one/undertaking_file_security.py").read_text()
undertaking = (ROOT / "wafd_one/wafd_one/doctype/wafd_hotel_undertaking/wafd_hotel_undertaking.py").read_text()
undertaking_js = (ROOT / "wafd_one/wafd_one/doctype/wafd_hotel_undertaking/wafd_hotel_undertaking.js").read_text()
nav = (ROOT / "wafd_one/public/js/wafd_mobile_navigation.js").read_text()
css = (ROOT / "wafd_one/public/css/wafd_mobile_navigation.css").read_text()
patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc343/execute.py").read_text()

assert "prepared_by_user" in security and "prepared_by_user" in file_security
assert '{"signature_image": ["!=", ""]}' in undertaking
assert "wafd_open_undertaking_preview(frm)" in undertaking_js
assert "wafd_keep_created_undertaking_open(frm)" in undertaking_js
assert 'route[1] === "WAFD Hotel Undertaking"' in nav
assert "wafd-mobile-document-shell" in nav and "wafd-mobile-document-shell" in css
for token in ("data-wafd-field-home", "wafd-field-language", "data-wafd-field-logout", "wafd-pwa-account"):
    assert token in nav
assert "include_signature\": 1" in patch and "compiled_html=''" in patch

print("RC343 undertaking signature, visibility and mobile menu checks passed")
