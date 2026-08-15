#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]
page_expected={
 'wafd_one_dashboard': {'System Manager','WAFD Operations Manager','WAFD Project Manager','WAFD Production Supervisor','WAFD Quality Inspector','WAFD Delivery Supervisor','WAFD Driver','WAFD Finance User','WAFD Storekeeper','WAFD Approver','WAFD Auditor'},
 'wafd_iftar_wizard': {'System Manager','WAFD Operations Manager','WAFD Project Manager'},
 'wafd_iftar_operations': {'System Manager','WAFD Operations Manager','WAFD Project Manager','WAFD Delivery Supervisor','WAFD Storekeeper'},
}
for page,expected in page_expected.items():
    fp=ROOT/'wafd_one'/'wafd_one'/'page'/page/f'{page}.json'
    data=json.loads(fp.read_text(encoding='utf-8'))
    actual={r['role'] for r in data.get('roles',[])}
    if actual != expected: errors.append(f'{page}: roles mismatch {actual ^ expected}')
patch=(ROOT/'wafd_one'/'patches'/'v10_0_0_rc152'/'execute.py').read_text(encoding='utf-8')
for master in ('Item','Item Group','UOM','Warehouse'):
    if f'"{master}"' not in patch: errors.append(f'missing standard lookup policy for {master}')
if 'setup_custom_perms(doctype)' not in patch:
    errors.append('standard Custom DocPerm seeding missing; native ERPNext roles could be overwritten')
if errors:
    print('RC152 SURFACE AUDIT FAILED')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('RC152 SURFACE AUDIT PASSED: pages + standard master lookup policy checked')
