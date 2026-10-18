"""RC388 regression: keep the external viewer appbar outside Frappe's page grid."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / 'wafd_one/public/wafd_mobile_navigation.bundle.js'
SOURCE = ROOT / 'wafd_one/public/js/wafd_mobile_navigation.js'


def test_appbar_patch_matches_in_source_and_bundle():
    def fragment(path):
        return path.read_text().split("function syncFieldAppbar(show) {", 1)[1].split("\n  function ", 1)[0]
    assert fragment(SOURCE) == fragment(BUNDLE)


def test_authority_appbar_is_mounted_outside_page_container():
    js = BUNDLE.read_text()
    fn = js.split('function syncFieldAppbar(show) {', 1)[1].split('\n  function ', 1)[0]
    assert 'currentRouteName() === IFTAR_AUTHORITY_VIEWER_ROUTE' in fn
    assert 'bar.parentElement !== document.body' in fn
    assert 'document.body.prepend(bar)' in fn
    assert 'if (authorityViewer)' in fn


def test_other_field_roles_keep_existing_page_mounting():
    js = BUNDLE.read_text()
    fn = js.split('function syncFieldAppbar(show) {', 1)[1].split('\n  function ', 1)[0]
    assert 'const activePage = Array.from(document.querySelectorAll(".page-container"))' in fn
    assert 'const target = activePage || document.body' in fn
    assert 'target.prepend(bar)' in fn
    assert 'if (!show || !isMobile())' in fn
