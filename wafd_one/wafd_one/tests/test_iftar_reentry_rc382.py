from pathlib import Path


def test_external_viewer_native_capture_is_limited_to_viewer_card():
    src = (Path(__file__).resolve().parents[1] / "page" / "wafd_role_home" / "wafd_role_home.js").read_text()
    assert 'data-wafd-iftar-viewer="1"' in src
    assert 'window.__wafdIftarViewerDocumentNavigation383' in src
    assert 'document.addEventListener("click"' in src
    assert '}, true);' in src
    assert 'event.stopImmediatePropagation()' in src
    assert 'window.location.assign("/app/wafd-iftar-authority-viewer")' in src
