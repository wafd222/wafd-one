from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'page' / 'wafd_iftar_authority_viewer'


def test_viewer_repairs_outer_desk_shell_on_load_and_show():
    js = (PAGE / 'wafd_iftar_authority_viewer.js').read_text()
    assert 'function wafdFitExternalIftarViewer(wrapper)' in js
    assert "wrapper.querySelectorAll('.layout-side-section" in js
    assert "'display':'none'" in js
    assert "'grid-template-columns':'minmax(0, 1fr)'" in js
    assert 'wafdFitExternalIftarViewer(wrapper);' in js
    assert 'wafdFitExternalIftarViewer(shownWrapper || wrapper);' in js
    assert 'requestAnimationFrame(() => wafdFitExternalIftarViewer(wrapper))' in js
    assert 'wafdAuthorityMobileOriginalStyles' in js


def test_existing_external_viewer_report_and_permissions_unchanged():
    js = (PAGE / 'wafd_iftar_authority_viewer.js').read_text()
    assert 'get_authority_monitoring_data' in js
    assert 'get_authority_final_report_html' in js
    assert 'get_authority_final_report_pdf' in js
    assert 'stage(t("reportFinal"),finalReady' in js
    assert 'class="wafv-auth-share"' not in js
