"""Regression checks for authority viewer stage evidence payload."""
from pathlib import Path


def test_authority_monitoring_payload_exposes_only_evidence_presence_flags():
    source = Path(__file__).resolve().parents[1].joinpath("iftar_stage_portal.py").read_text(encoding="utf-8")
    assert '"closeout_photo": bool(report.closeout_photo)' in source
    assert '"preservation_receipt_photo": bool(report.preservation_receipt_photo)' in source
    assert '"preservation_receiver_signature": bool(report.preservation_receiver_signature)' in source


def test_authority_viewer_checks_closeout_and_preservation_evidence_flags():
    source = Path(__file__).resolve().parents[1].joinpath("page", "wafd_iftar_authority_viewer", "wafd_iftar_authority_viewer.js").read_text(encoding="utf-8")
    assert "r.closeout_photo===true" in source
    assert "r.preservation_receipt_photo===true" in source
    assert "r.preservation_receiver_signature===true" in source
