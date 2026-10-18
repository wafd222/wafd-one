from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_role_home_card_handler_survives_replaced_page_body():
    source = (ROOT / "page" / "wafd_role_home" / "wafd_role_home.js").read_text(encoding="utf-8")
    assert '$(document).off("click.wafdMobileCard", ".wafd-role-home-page .wafd-mobile-card").on("click.wafdMobileCard", ".wafd-role-home-page .wafd-mobile-card"' in source
    assert 'frappe.pages["wafd-role-home"].on_page_show' in source
    assert 'wafdRestoreRoleHomeInteractivity();' in source

def test_authority_viewer_rebinds_report_clicks_after_cached_route_show():
    source = (ROOT / "page" / "wafd_iftar_authority_viewer" / "wafd_iftar_authority_viewer.js").read_text(encoding="utf-8")
    assert 'root.off("click.wafvReport", ".wafv-stage-report").on("click.wafvReport", ".wafv-stage-report"' in source
    assert 'frappe.pages["wafd-iftar-authority-viewer"].on_page_show' in source
    assert 'wafdAuthorityViewerRefresh(wrapper, !firstShow)' in source
    assert 'load(root.find("#wafv-auth-date").val() || lastLoadedDate || "")' in source

def test_report_return_releases_freeze_and_reconnects_live_root():
    source = (ROOT / "page" / "wafd_iftar_authority_viewer" / "wafd_iftar_authority_viewer.js").read_text(encoding="utf-8")
    assert 'syncMobileSurface();' in source and 'root = $liveRoot;' not in source
    assert 'restoreAfterReport(true);' in source
    assert 'root.css({"pointer-events":"", "opacity":""}).removeAttr("aria-busy")' in source
