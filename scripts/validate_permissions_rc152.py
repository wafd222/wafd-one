#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCTYPE_ROOT=ROOT/'wafd_one'/'wafd_one'/'doctype'
WAFD_ROLES={
 'WAFD Operations Manager','WAFD Project Manager','WAFD Production Supervisor','WAFD Quality Inspector',
 'WAFD Delivery Supervisor','WAFD Driver','WAFD Finance User','WAFD Storekeeper','WAFD Approver','WAFD Auditor'
}
errors=[]
count=0
for fp in sorted(DOCTYPE_ROOT.glob('*/*.json')):
    data=json.loads(fp.read_text(encoding='utf-8'))
    if data.get('istable') or not data.get('name'):
        continue
    count += 1
    dt=data['name']; perms=data.get('permissions') or []
    roles=[p.get('role') for p in perms]
    if len(roles)!=len(set(roles)):
        errors.append(f'{dt}: duplicate role permission row')
    for required in ('System Manager','WAFD Operations Manager'):
        row=next((p for p in perms if p.get('role')==required),None)
        if not row or not row.get('read') or not row.get('write') or not row.get('create'):
            errors.append(f'{dt}: {required} must have read/write/create')
    for p in perms:
        role=p.get('role')
        if role in WAFD_ROLES and role not in {'WAFD Operations Manager','WAFD Auditor'}:
            for right in ('delete','import','share','email','export'):
                if p.get(right):
                    errors.append(f'{dt}: {role} unexpectedly has {right}')

# Critical segregation assertions
def perms(dt,role):
    fp=next(DOCTYPE_ROOT.glob(f'*/{dt.lower().replace(" ","_")}.json'),None)
    if fp is None:
        for f in DOCTYPE_ROOT.glob('*/*.json'):
            d=json.loads(f.read_text(encoding='utf-8'))
            if d.get('name')==dt: fp=f; break
    d=json.loads(fp.read_text(encoding='utf-8'))
    return next((p for p in d.get('permissions',[]) if p.get('role')==role),{})

for role in ('WAFD Production Supervisor','WAFD Storekeeper'):
    p=perms('WAFD Recipe',role)
    if not p.get('read') or p.get('write') or p.get('create') or p.get('delete'):
        errors.append(f'WAFD Recipe: {role} must be read-only')

for dt,role in [
 ('WAFD Production Batch','WAFD Production Supervisor'),('WAFD Quality Inspection','WAFD Quality Inspector'),
 ('WAFD Stock Movement','WAFD Storekeeper'),('WAFD Delivery Trip','WAFD Delivery Supervisor'),
 ('WAFD Invoice','WAFD Finance User'),('WAFD Catering Project','WAFD Project Manager')]:
    p=perms(dt,role)
    if not (p.get('read') and p.get('write') and p.get('create')):
        errors.append(f'{dt}: {role} must have operational read/write/create')

if errors:
    print('RC152 PERMISSION AUDIT FAILED')
    for e in errors: print('-',e)
    raise SystemExit(1)
print(f'RC152 PERMISSION AUDIT PASSED: {count} non-child WAFD DocTypes checked')
