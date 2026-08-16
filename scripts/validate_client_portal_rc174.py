from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
backend = (ROOT / "wafd_one" / "client_portal.py").read_text(encoding="utf-8")
portal = (ROOT / "wafd_one" / "www" / "wafd_client.html").read_text(encoding="utf-8")
role_home = (ROOT / "wafd_one" / "wafd_one" / "page" / "wafd_role_home" / "wafd_role_home.js").read_text(encoding="utf-8")
version = (ROOT / "wafd_one" / "__init__.py").read_text(encoding="utf-8")

assert '10.0.0rc174' in version
assert '_event_matches_trip_day' in backend
assert '_safe_duration_payload' in backend
assert 'TIMING_NOT_COMPARABLE' in backend
assert '"actual_departure": start' in backend
assert '"actual_arrival": clean_arrival' in backend
assert 'trip_details[0] if trip_details else None' in backend
for code in ('ar','en','id','ur','hi','bn','fr','ha','sw','uz'):
    assert f"{code}:" in portal or f"{code}:'" in portal or f'{code}:"' in portal
assert 'localStorage.setItem(\'wafd_lang\'' in portal
assert 'wcp-language' in portal
assert 'wafd-role-lang' in role_home
assert 'localStorage.setItem("wafd_lang"' in role_home
print('RC174 multilingual + timing integrity validation: PASS')
