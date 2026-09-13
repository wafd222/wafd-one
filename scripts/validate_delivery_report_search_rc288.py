"""Static validation for the RC288 delivery report corrections."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
report = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_report/wafd_delivery_report.js").read_text(encoding="utf-8")
page_json = (ROOT / "wafd_one/wafd_one/page/wafd_delivery_report/wafd_delivery_report.json").read_text(encoding="utf-8")
navigation = (ROOT / "wafd_one/public/js/wafd_mobile_navigation.js").read_text(encoding="utf-8")
bundle = (ROOT / "wafd_one/public/wafd_mobile_navigation.bundle.js").read_text(encoding="utf-8")

assert "renderHotelResults" in report
assert "slice(0,10)" in report
assert "q.length<2" in report
assert "data-hotel-choice" in report
assert "تقرير رسمي بنفس هوية تعهد الفندق" not in report
assert '"title": "تقارير التوصيل"' in page_json
assert 'DELIVERY_REPORT_ROUTE = "wafd-delivery-report"' in navigation
assert "isDeliverySupervisorShell" in navigation
assert "deliverySupervisorShell" in navigation
assert navigation == bundle
print("RC288 delivery report search and isolation checks passed")
