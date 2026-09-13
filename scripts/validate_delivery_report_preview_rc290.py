"""Static validation for the RC290 mobile report preview."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
report_js = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_report/wafd_delivery_report.js").read_text(encoding="utf-8")
report_css = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_report/wafd_delivery_report.css").read_text(encoding="utf-8")
report_py = (ROOT / "wafd_one/delivery_report.py").read_text(encoding="utf-8")

assert "preview_delivery_report_html" in report_js
assert "function fitPreviewFrame(frame)" in report_js
assert 'sheet.style.width="210mm"' in report_js
assert "available/naturalWidth" in report_js
assert "function printPreviewFrame(frame,pdf)" in report_js
assert "z-index: 2200" in report_css
assert "env(safe-area-inset-top)" in report_css
assert "overflow: hidden" in report_css
assert "def preview_delivery_report_html(" in report_py
assert 'frappe.local.response.content_type = "text/html; charset=utf-8"' in report_py
assert "meta name='viewport'" in report_py
print("RC290 delivery report mobile preview checks passed")
