from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'page' / 'wafd_iftar_authority_viewer'


def test_external_viewer_mobile_shell_full_width_scoped():
    css = (BASE / 'wafd_iftar_authority_viewer.css').read_text()
    assert '.wafd-authority-viewer-page .layout-side-section' in css
    assert '.wafd-authority-viewer-page .layout-main-section-wrapper' in css
    assert 'flex:0 0 100% !important' in css
    assert '.wafd-authority-viewer-page .wafv-auth-summary-wrap' in css
    assert 'overflow-x:auto' in css


def test_external_report_stage_kept_and_redundant_share_removed():
    js = (BASE / 'wafd_iftar_authority_viewer.js').read_text()
    assert 'stage(t("reportFinal"),finalReady' in js
    assert 'openOfficialReportPreview(project,op)' in js
    assert '".wafv-stage-report"' in js
    assert 'class="wafv-auth-share"' not in js
    assert 'root.off("click.wafvReport", ".wafv-auth-share")' not in js
    # Keep sharing from the report preview toolbar; only the duplicate page button is removed.
    assert '<button id="share">' in js
