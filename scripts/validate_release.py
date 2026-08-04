from __future__ import annotations
import ast, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors=[]

def fail(msg): errors.append(msg)

# Version consistency
pyproject=(ROOT/'pyproject.toml').read_text(encoding='utf-8')
init=(ROOT/'wafd_one/__init__.py').read_text(encoding='utf-8')
readme=(ROOT/'README.md').read_text(encoding='utf-8')
m1=re.search(r'version\s*=\s*"([^"]+)"',pyproject)
m2=re.search(r'__version__\s*=\s*"([^"]+)"',init)
if not m1 or not m2 or m1.group(1)!=m2.group(1): fail('Version mismatch between pyproject.toml and __init__.py')
release=(m1.group(1) if m1 else '').replace('rc',' RC')
if release and release not in readme: fail(f'README does not declare {release}')

# Python syntax
for path in ROOT.rglob('*.py'):
    try: ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    except Exception as exc: fail(f'Python syntax: {path.relative_to(ROOT)}: {exc}')

# JSON syntax
for path in ROOT.rglob('*.json'):
    try: json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: fail(f'JSON: {path.relative_to(ROOT)}: {exc}')

# Patch targets
section=False
for raw in (ROOT/'wafd_one/patches.txt').read_text(encoding='utf-8').splitlines():
    line=raw.strip()
    if line=='[post_model_sync]': section=True; continue
    if line.startswith('['): section=False
    if not section or not line or line.startswith('#'): continue
    rel=Path(*line.split('.'))
    if not ((ROOT/(str(rel)+'.py')).exists() or (ROOT/rel/'__init__.py').exists()):
        fail(f'Missing patch module: {line}')

# Fixed Document Studio template IDs are forbidden in client code.
for path in ROOT.rglob('*.js'):
    text=path.read_text(encoding='utf-8')
    if re.search(r'template_name=WDT-\d+', text): fail(f'Hard-coded template ID: {path.relative_to(ROOT)}')

if errors:
    print('\n'.join(f'ERROR: {e}' for e in errors))
    sys.exit(1)
print('Release validation passed.')
