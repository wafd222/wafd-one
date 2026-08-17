from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
hooks=(root/'wafd_one/hooks.py').read_text()
mobile=(root/'wafd_one/www/wafd_mobile.py').read_text()
manifest=json.loads((root/'wafd_one/public/pwa/manifest.webmanifest').read_text())
css=(root/'wafd_one/wafd_one/page/wafd_one_dashboard/wafd_one_dashboard.css').read_text()
assert 'app_home = "/app/wafd-role-home"' in hooks
assert '"route": "/app/wafd-role-home"' in hooks
assert '/desk/wafd-role-home' not in hooks
assert 'target = "/app/wafd-role-home"' in mobile
assert manifest['start_url']=='/app/wafd-role-home'
assert manifest['id']=='/app/wafd-role-home'
assert 'RC181 — mobile System Sections alignment' in css
print('RC181 mobile launch + card validation passed')
