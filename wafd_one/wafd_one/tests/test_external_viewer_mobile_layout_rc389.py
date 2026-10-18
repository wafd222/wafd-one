from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "page/wafd_iftar_authority_viewer/wafd_iftar_authority_viewer.js").read_text()
CSS = (ROOT / "page/wafd_iftar_authority_viewer/wafd_iftar_authority_viewer.css").read_text()

def test_isolated_surface_does_not_override_frappe_page_display():
    assert "appendTo(document.body)" in JS
    assert "wafv-mobile-surface" in JS
    assert "setStyles(wrapper" not in JS
    assert "wafdFitExternalIftarViewer" not in JS
    assert "body > .wafv-mobile-surface:not([hidden])" in CSS

def test_mobile_route_lifecycle_and_report_stage_preserved():
    assert "frappe.router.on('change', scheduleSurfaceSync)" in JS
    assert "on_page_hide" in JS
    assert "wafv-stage-report" in JS
    assert "wafd-authority-report-return" in JS
    assert "frappe.set_route('wafd-role-home')" in JS

def test_mobile_surface_full_viewport_and_desktop_preserved():
    assert "width:100vw !important" in CSS
    assert "height:100dvh !important" in CSS
    assert "@media (max-width:900px)" in CSS
    assert "wafv-mobile-surface[hidden]" in CSS
