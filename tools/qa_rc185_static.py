from pathlib import Path
import ast, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
errors=[]

# Release metadata
expected='10.0.0rc185'
init=(ROOT/'wafd_one/__init__.py').read_text()
pyproject=(ROOT/'pyproject.toml').read_text()
if expected not in init: errors.append('version missing from __init__.py')
if f'version = "{expected}"' not in pyproject: errors.append('version mismatch in pyproject.toml')

# Python / JSON syntax
py_count=json_count=0
for p in ROOT.rglob('*.py'):
    if any(part in {'.git','node_modules'} for part in p.parts): continue
    py_count += 1
    try: ast.parse(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'Python parse failed {p.relative_to(ROOT)}: {e}')
for p in ROOT.rglob('*.json'):
    if any(part in {'.git','node_modules'} for part in p.parts): continue
    json_count += 1
    try: json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'JSON parse failed {p.relative_to(ROOT)}: {e}')

# Current mobile role home architecture
js=(ROOT/'wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js').read_text()
css=(ROOT/'wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.css').read_text()
required_roles=[
    'System Manager','WAFD Operations Manager','WAFD Project Manager',
    'WAFD Production Supervisor','WAFD Quality Inspector','WAFD Storekeeper',
    'WAFD Cleaning Supervisor','WAFD Delivery Supervisor','WAFD Driver',
    'WAFD Finance User','WAFD Approver','WAFD Auditor'
]
for role in required_roles:
    if role not in js: errors.append(f'role home missing role: {role}')
if '/assets/wafd_one/images/wafd-almadinah-dashboard.png' not in js:
    errors.append('approved logo asset missing from role home')
if 'wafd-role-home-page' not in js or 'wafd-role-home-page' not in css:
    errors.append('RC185 scoped mobile page class missing')
if 'margin-inline-start:6px' not in css:
    errors.append('RC185 logo safe inset missing')
if '::-webkit-scrollbar' not in css or 'scrollbar-width:none' not in css:
    errors.append('RC185 scrollbar cleanup missing')

# Row-level security hooks and implementations
hooks=(ROOT/'wafd_one/hooks.py').read_text()
driver=(ROOT/'wafd_one/driver_security.py').read_text()
cleaning=(ROOT/'wafd_one/cleaning_security.py').read_text()
checks={
 'driver trip query hook':'wafd_one.driver_security.delivery_trip_query',
 'driver trip permission hook':'wafd_one.driver_security.delivery_trip_has_permission',
 'driver proof query hook':'wafd_one.driver_security.delivery_proof_query',
 'cleaning warehouse query hook':'wafd_one.cleaning_security.warehouse_query',
 'cleaning stock balance query hook':'wafd_one.cleaning_security.stock_balance_query',
 'cleaning movement query hook':'wafd_one.cleaning_security.stock_movement_query',
}
for name, token in checks.items():
    if token not in hooks: errors.append(f'missing {name}')
if 'return "1=0"' not in driver or '`tabWAFD Delivery Trip`.`driver`' not in driver:
    errors.append('driver row-level denial/filter guard missing')
if 'issued_to_user' not in cleaning or 'CLEANING_TYPE' not in cleaning:
    errors.append('cleaning row-level restriction guard missing')

# Patch list sanity
patches=(ROOT/'wafd_one/patches.txt')
entries=[]
if patches.exists():
    for line in patches.read_text().splitlines():
        s=line.strip()
        if s and not s.startswith('#') and not (s.startswith('[') and s.endswith(']')): entries.append(s)
    if len(entries) != len(set(entries)): errors.append('duplicate patch entries found')
    for entry in entries:
        rel=Path(*entry.split('.'))
        candidates=[ROOT/(str(rel)+'.py'), ROOT/rel/'execute.py']
        if not any(c.exists() for c in candidates): errors.append(f'missing patch target: {entry}')

if errors:
    print('RC185 STATIC QA FAILED')
    for e in errors: print('-',e)
    sys.exit(1)
print(f'RC185 STATIC QA PASS — {py_count} Python files, {json_count} JSON files, {len(entries)} patch entries')
