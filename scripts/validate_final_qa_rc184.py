from __future__ import annotations
import ast, json, re, tomllib
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def check(cond, msg):
    if not cond:
        raise AssertionError(msg)

def main():
    project = tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))
    version = project['project']['version']
    check(version == '10.0.0rc184', f'Unexpected version: {version}')
    check((ROOT/'wafd_one/__init__.py').read_text(encoding='utf-8').strip() == '__version__ = "10.0.0rc184"', 'Python package version mismatch')
    check((ROOT/'RELEASE_NOTES_10.0.0rc184.md').exists(), 'RC184 release notes missing')
    check('10.0.0 RC184' in (ROOT/'README.md').read_text(encoding='utf-8')[:250], 'README current release mismatch')

    py_count=json_count=0
    for p in ROOT.rglob('*.py'):
        if any(part.startswith('.') for part in p.relative_to(ROOT).parts): continue
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p)); py_count += 1
    json_docs=[]
    for p in ROOT.rglob('*.json'):
        doc=json.loads(p.read_text(encoding='utf-8')); json_count += 1
        if isinstance(doc,dict): json_docs.append((p,doc))

    patches=[]
    for raw in (ROOT/'wafd_one/patches.txt').read_text(encoding='utf-8').splitlines():
        x=raw.strip()
        if not x or x.startswith('#') or (x.startswith('[') and x.endswith(']')): continue
        patches.append(x)
    dup=[x for x,n in Counter(patches).items() if n>1]
    check(not dup, f'Duplicate patches: {dup}')
    missing=[]
    for mod in patches:
        path=ROOT/Path(*mod.split('.'))
        if not (path.with_suffix('.py').exists() or (path/'__init__.py').exists()): missing.append(mod)
    check(not missing, f'Missing patch modules: {missing}')

    hooks=(ROOT/'wafd_one/hooks.py').read_text(encoding='utf-8')
    mobile=(ROOT/'wafd_one/www/wafd_mobile.py').read_text(encoding='utf-8')
    manifest=json.loads((ROOT/'wafd_one/public/pwa/manifest.webmanifest').read_text(encoding='utf-8'))
    check('app_home = "/desk/wafd-role-home"' in hooks, 'app_home is not the Frappe v16 Desk route')
    check('"route": "/desk/wafd-role-home"' in hooks, 'Apps screen route mismatch')
    check('target = "/desk/wafd-role-home"' in mobile, 'Legacy mobile redirect mismatch')
    check(manifest.get('start_url') == '/desk/wafd-role-home' and manifest.get('id') == '/desk/wafd-role-home', 'PWA route mismatch')
    check('{"from_route": "/app/wafd-role-home", "to_route": "wafd_mobile"}' in hooks, 'RC181 compatibility redirect missing')

    role_css=(ROOT/'wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.css').read_text(encoding='utf-8')
    role_js=(ROOT/'wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js').read_text(encoding='utf-8')
    check('overflow:visible' in role_css and 'object-fit:contain' in role_css and 'padding:5px' in role_css, 'RC183 full-logo containment fix missing')
    check('/assets/wafd_one/images/wafd-almadinah-dashboard.png' in role_js, 'Role-home WAFD logo asset missing')

    for token in ('WAFD Delivery Trip', 'WAFD Delivery Proof'):
        check(token in hooks, f'Driver row security hook missing for {token}')
    for token in ('WAFD Warehouse', 'WAFD Stock Balance', 'WAFD Stock Movement'):
        check(token in hooks, f'Cleaning row security hook missing for {token}')
    check('permission_query_conditions = {' in hooks and 'has_permission = {' in hooks, 'Row-level security hooks missing')

    required={'WAFD Catering Project','WAFD Daily Meal Plan','WAFD Production Batch','WAFD Quality Inspection','WAFD Packaging Record','WAFD Loading Record','WAFD Delivery Trip','WAFD Delivery Note','WAFD Receiving Note','WAFD Invoice','WAFD Payment','WAFD Hotel Undertaking'}
    names={d.get('name') for _,d in json_docs}
    check(not (required-names), f'Missing core operational metadata: {sorted(required-names)}')

    hotel_csv=ROOT/'wafd_one/reference_data/madinah_hotels_400_ota_review.csv'
    check(hotel_csv.exists(), '400-hotel reference dataset missing')
    rows=hotel_csv.read_text(encoding='utf-8-sig').splitlines()
    check(len(rows)==401, f'Expected header + 400 hotel rows, got {len(rows)} lines')

    portal=(ROOT/'wafd_one/www/wafd_client.py').read_text(encoding='utf-8') if (ROOT/'wafd_one/www/wafd_client.py').exists() else ''
    check('WAFD Client Portal User' in hooks, 'Client portal role/menu isolation missing')

    print(f'RC184 FINAL STATIC QA PASS — {py_count} Python files, {json_count} JSON files, {len(patches)} patch entries')

if __name__=='__main__': main()
