from pathlib import Path


def test_external_viewer_has_native_href_without_capture_interceptor():
    src = (Path(__file__).resolve().parents[1] / 'page' / 'wafd_role_home' / 'wafd_role_home.js').read_text()
    assert 'href="/app/wafd-iftar-authority-viewer"' in src
    assert 'data-wafd-iftar-viewer="1"' in src
    assert 'window.__wafdIftarViewerDocumentNavigation383' not in src
    assert 'event.stopImmediatePropagation()' not in src


def test_report_return_does_not_replace_popup_with_opener_url():
    src = (Path(__file__).resolve().parents[1] / 'page' / 'wafd_iftar_authority_viewer' / 'wafd_iftar_authority_viewer.js').read_text()
    assert 'window.location.replace(target)' not in src
    assert 'window.location.replace(u)' not in src
    assert 'wafd-authority-report-return' in src
