from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / "wafd_one/templates/print_formats/wafd_iftar_official_daily_report.html").read_text()

assert "height:22mm" in template
assert "max-height:13mm" in template
assert "margin-top:1.5mm" in template or '<div class="footer">' not in template
assert "page-break-inside:avoid" in template
assert "format_datetime(o.delivery_time" not in template
assert "o.get_formatted('delivery_time')" in template

print("RC339 official report pagination checks passed")
