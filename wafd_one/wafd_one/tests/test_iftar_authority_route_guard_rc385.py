from pathlib import Path
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[2]


def test_active_frappe_hook_loads_corrected_bundle():
    hooks = (ROOT / 'hooks.py').read_text(encoding='utf-8')
    assert '"wafd_mobile_navigation.bundle.js"' in hooks
    bundle = (ROOT / 'public/wafd_mobile_navigation.bundle.js').read_text(encoding='utf-8')
    source = (ROOT / 'public/js/wafd_mobile_navigation.js').read_text(encoding='utf-8')
    for js in (bundle, source):
        assert 'const IFTAR_AUTHORITY_VIEWER_ROUTE = "wafd-iftar-authority-viewer"' in js
        assert '(window.frappe?.user_roles || []).includes("WAFD Iftar Authority Viewer")' in js
        assert 'pathIsRoute(IFTAR_AUTHORITY_VIEWER_ROUTE)' in js


def test_real_mobile_route_guard_reentry_and_permissions():
    if not shutil.which('node'):
        import pytest
        pytest.skip('Node.js is required for the executable mobile-navigation regression test')
    test = Path(__file__).with_suffix('.js')
    subprocess.run(['node', str(test)], check=True, capture_output=True, text=True, timeout=15)
