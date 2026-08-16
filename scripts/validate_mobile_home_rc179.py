from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js').read_text(encoding='utf-8')
CSS = (ROOT / 'wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.css').read_text(encoding='utf-8')

# Explanatory microcopy must not be rendered anymore.
for banned in [
    'wafd-mobile-section-head',
    'wafd-mobile-security-note',
    'profile.subtitle ||',
    'tr("مهامك")',
    'tr("الأدوات الظاهرة مرتبطة بصلاحيات حسابك فقط")',
]:
    assert banned not in JS, banned

# Core role-based cards and routing remain intact.
for required in [
    'WAFD Operations Manager', 'WAFD Finance User', 'WAFD Driver',
    'wafd-one-dashboard', 'wafd-operations-hub', 'wafd-inventory-hub',
    'wafd-delivery-hub', 'wafd-finance-hub', 'wafd-iftar-operations'
]:
    assert required in JS, required

# Language control is still present and has the mobile anti-clipping override.
assert 'id="wafd-role-lang"' in JS
assert '.wafd-mobile-lang{position:relative' in CSS
assert '.wafd-mobile-brand p,.wafd-mobile-section-head,.wafd-mobile-security-note{display:none!important}' in CSS

print('RC179 mobile home polish validation passed')
