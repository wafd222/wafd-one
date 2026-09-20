from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


template = read("wafd_one/templates/print_formats/wafd_iftar_official_daily_report.html")
page = read("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js")
patch = read("wafd_one/wafd_one/patches/v10_0_0_rc338/execute.py")

# A Frappe Time child field is a datetime.timedelta in Python. It must never be
# passed to format_datetime, which caused the reported PrintFormatError.
assert "format_datetime(o.delivery_time" not in template
assert "o.get_formatted('delivery_time')" in template
assert "doc.get_formatted('operation_date')" in template

# The mobile toolbar must only enable native sharing after a real, non-empty
# PDF was prefetched. An HTML traceback must not be shared as if it were a PDF.
assert 'type.includes("application/pdf")' in page
assert 'if(!blob.size)' in page
assert '$share.prop("disabled",true)' in page
assert '$share.prop("disabled",false)' in page
assert 'navigator.canShare({files:[file]})' in page

assert 'height:40mm' in template
assert 'height:27mm' in template
assert 'reload_doc("wafd_one", "print_format", "wafd_iftar_official_daily_report"' in patch

print("RC338 official PDF generation and native sharing checks passed")
