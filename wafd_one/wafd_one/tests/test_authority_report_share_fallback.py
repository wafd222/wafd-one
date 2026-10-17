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
