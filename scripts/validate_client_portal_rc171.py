from pathlib import Path
html = Path('wafd_one/www/wafd_client.html').read_text(encoding='utf-8')
py = Path('wafd_one/www/wafd_client.py').read_text(encoding='utf-8')
backend = Path('wafd_one/client_portal.py').read_text(encoding='utf-8')
assert '/api/method/wafd_one.client_portal.' in html
assert 'fetch(url,options)' in html
assert 'frappe.call' not in html
assert 'frappe.msgprint' not in html
assert 'frappe.show_alert' not in html
assert "credentials:'same-origin'" in html
assert "X-Frappe-CSRF-Token" in html
assert 'WAFD Client Portal User' in py
assert 'WAFD Client Portal Access' in backend
assert '_get_access(project, user)' in backend
print('RC171 client portal validation: PASS')
