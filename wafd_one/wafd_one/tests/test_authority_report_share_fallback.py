"""Regression checks for authority report sharing in restricted browsers."""
from pathlib import Path


def test_authority_report_share_api_failure_falls_back_to_pdf_download():
    source = Path(__file__).resolve().parents[1].joinpath(
        "page", "wafd_iftar_authority_viewer", "wafd_iftar_authority_viewer.js"
    ).read_text(encoding="utf-8")
    assert "catch(shareError)" in source
    assert "fall back to PDF download" in source
    assert "Direct sharing is blocked" in source
    assert "تعذرت المشاركة المباشرة" in source


def test_authority_report_return_clears_stale_frappe_freeze_and_avoids_history_back():
    source = Path(__file__).resolve().parents[1].joinpath(
        "page", "wafd_iftar_authority_viewer", "wafd_iftar_authority_viewer.js"
    ).read_text(encoding="utf-8")
    assert "restoreAfterReport" in source
    assert "frappe.dom.unfreeze()" in source
    assert "visibilitychange" in source
    assert "pageshow" in source
    assert "history.back()" not in source
    assert "freeze:false" in source


def test_authority_report_embeds_images_from_frappe_storage_backend():
    source = Path(__file__).resolve().parents[1].joinpath("iftar_stage_portal.py").read_text(encoding="utf-8")
    helper = source[source.index("def _embed_iftar_report_images"):source.index("def _get_authority_final_report_html")]
    assert "unquote(parsed.path or src)" in helper
    assert "file_doc.get_content()" in helper
    assert "base64.b64encode(image_bytes)" in helper
