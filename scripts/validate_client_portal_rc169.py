from pathlib import Path
import json, re
root=Path(__file__).resolve().parents[1]
assert '10.0.0rc169' in (root/'wafd_one/__init__.py').read_text()
hooks=(root/'wafd_one/hooks.py').read_text()
assert '/wafd-client' in hooks and 'WAFD Client Portal User' in hooks
api=(root/'wafd_one/client_portal.py').read_text()
for token in ['_get_access(', 'WAFD Client Portal Access', 'WAFD Client Receipt Acknowledgement', 'acknowledge_receipt']:
    assert token in api, token
for forbidden in ['contract_value', 'estimated_cost', 'actual_cost', 'profit_margin_percent', 'cost_per_meal', 'WAFD Stock Balance', 'WAFD Supplier']:
    assert forbidden not in api, f'portal API exposes forbidden token: {forbidden}'
for name in ['wafd_client_portal_access','wafd_client_receipt_acknowledgement']:
    p=root/'wafd_one/wafd_one/doctype'/name/(name+'.json')
    data=json.loads(p.read_text())
    assert data['module']=='WAFD ONE'
html=(root/'wafd_one/wafd_one/www/wafd_client.html').read_text()
assert 'بوابة متابعة الوجبات' in html and 'acknowledge_receipt' in html
patches=(root/'wafd_one/patches.txt').read_text()
assert 'v10_0_0_rc169.execute' in patches
print('RC169 client portal validation: OK')
