from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


template = read("wafd_one/templates/print_formats/wafd_iftar_official_daily_report.html")
page = read("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js")
patch = read("wafd_one/wafd_one/patches/v10_0_0_rc336/execute.py")

for forbidden in (
    "وفق متطلبات التقرير الرسمي",
    "صور توثيق إضافية مرتبة ضمن مراحل التشغيل",
    "لا توجد صورة وصول محفوظة",
    "أُعد هذا التقرير من السجلات",
):
    assert forbidden not in template, forbidden

assert "التوثيق الميداني" in template
assert "format_datetime(o.delivery_time" not in template
assert "o.get_formatted('delivery_time')" in template
assert "new-page" in template and "keep-block" in template
assert "p.photo not in used_photos" in template
assert "data-report-share disabled" in page
assert "cachedPdf" in page and "pdfReady" in page
share_handler = page.split('$screen.on("click","[data-report-share]"', 1)[1].split(";\n", 1)[0]
assert "navigator.share" in share_handler
assert "async" not in share_handler.split("=>", 1)[0]
assert 'reload_doc("wafd_one", "print_format", "wafd_iftar_official_daily_report"' in patch

print("RC336 report cleanup, pagination, and native share checks passed")
