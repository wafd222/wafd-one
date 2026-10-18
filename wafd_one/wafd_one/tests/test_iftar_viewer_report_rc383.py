from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_external_viewer_reentry_handles_stale_ios_route():
    source = (ROOT / "page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
    assert 'currentRoute[0] === "wafd-iftar-authority-viewer"' in source
    assert 'frappe.set_route("wafd-role-home")' in source
    assert 'window.setTimeout(() => frappe.set_route("wafd-iftar-authority-viewer"), 120)' in source


def test_final_report_preview_stays_inside_app_and_has_return_controls():
    source = (ROOT / "page/wafd_iftar_authority_viewer/wafd_iftar_authority_viewer.js").read_text(encoding="utf-8")
    preview = source.split("function openOfficialReportPreview", 1)[1].split("async function shareReport", 1)[0]
    assert 'className = "wafv-report-overlay"' in preview
    assert 'data-report-back' in preview
    assert 'data-report-print' in preview
    assert 'data-report-share' in preview
    assert "window.open(" not in preview
    assert "frame.srcdoc = reportDoc(reportHtml)" in preview


def test_official_report_flows_across_pages_without_large_forced_gaps():
    source = (ROOT.parent / "templates/print_formats/wafd_iftar_official_daily_report.html").read_text(encoding="utf-8")
    assert ".keep-block{page-break-inside:auto;break-inside:auto}" in source
    assert ".new-page{page-break-before:auto;break-before:auto}" in source
