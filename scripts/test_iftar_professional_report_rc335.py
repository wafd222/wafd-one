import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


template = read("wafd_one/templates/print_formats/wafd_iftar_official_daily_report.html")
format_doc = json.loads(read("wafd_one/wafd_one/print_format/wafd_iftar_official_daily_report/wafd_iftar_official_daily_report.json"))
page = read("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js")
css = read("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.css")
patch = read("wafd_one/wafd_one/patches/v10_0_0_rc335/execute.py")

assert 'templates/print_formats/wafd_iftar_official_daily_report.html' in format_doc["html"]
assert "شركة وفد المدينة لخدمات الإعاشة" in template
assert "WAFD AL-MADINAH CATERING SERVICES" in template
assert "wafd-almadinah-official.png" in template
assert "0500336989" in template and "wafd.almadinah@gmail.com" in template
assert "تقدم <b>شركة وفد المدينة لخدمات الإعاشة</b> هذا التقرير اليومي" in template
for stage in ("وصول الوجبات واستلام الموقع", "فحص واعتماد مفتش التغذية", "تسليم المشرفين والمساعدون", "تسليم أصحاب السفر", "التوزيع والإغلاق الميداني", "الملاحظات والاعتمادات النهائية"):
    assert stage in template
assert "WAFD Delivery Proof" in template and "doc.daily_photos" in template
assert "assistant_name" not in template
for action in ("data-report-back", "data-report-share", "data-report-print", "data-report-download"):
    assert action in page
assert "navigator.share" in page and "downloadReportBlob" in page
assert "ift-official-preview" in css
assert 'reload_doc("wafd_one", "print_format", "wafd_iftar_official_daily_report"' in patch

print("RC335 professional official report and preview checks passed")
