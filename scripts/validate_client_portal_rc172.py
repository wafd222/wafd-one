from pathlib import Path
root=Path(__file__).resolve().parents[1]
py=(root/'wafd_one'/'client_portal.py').read_text()
html=(root/'wafd_one'/'www'/'wafd_client.html').read_text()
assert '_latest_service_date' in py
assert 'delivery_timing' in py
assert 'delivery_duration_display' in py
assert 'بداية التوصيل' in html
assert 'المدة من بداية التوصيل حتى الاستلام' in html
assert "openProject(card.dataset.project)" in html
print('RC172 client portal tracking validation: PASS')
