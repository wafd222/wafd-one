import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


project = json.loads(read("wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json"))
trip = json.loads(read("wafd_one/wafd_one/doctype/wafd_delivery_trip/wafd_delivery_trip.json"))
report = json.loads(read("wafd_one/wafd_one/doctype/wafd_iftar_supervisor_daily_report/wafd_iftar_supervisor_daily_report.json"))
team = read("wafd_one/wafd_one/iftar_team.py")
portal = read("wafd_one/wafd_one/iftar_stage_portal.py")
team_js = read("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js")
driver_py = read("wafd_one/driver_portal.py")
driver_js = read("wafd_one/wafd_one/page/wafd_iftar_driver/wafd_iftar_driver.js")
site_js = read("wafd_one/wafd_one/page/wafd_iftar_site/wafd_iftar_site.js")
supervisor_js = read("wafd_one/wafd_one/page/wafd_iftar_supervisor/wafd_iftar_supervisor.js")

project_fields = {f.get("fieldname") for f in project["fields"]}
assert {
    "project_title", "contracting_entity", "distribution_site", "start_date", "end_date",
    "daily_meals", "sale_price_per_meal", "material_cost_total", "operating_cost_total",
    "total_project_cost", "total_revenue", "vat_amount", "expected_profit", "profit_margin",
}.issubset(project_fields)

# Project Manager: nested supervisors, assistants and table owners with quantities and locations.
for token in ("المشرفون والمساعدون", "أصحاب السفر وتوزيع الوجبات", "po-meals", "po-bread", "po-tables", "po-point"):
    assert token in team_js
assert '"project_manager_user"' in team and '"supervisor_plans"' in portal

# Kitchen and vehicle allocation stages.
for label in ("اعتماد الإنتاج", "اعتماد التغليف", "اعتماد التحميل", "توزيع الوجبات المحملة على السيارات"):
    assert label in team_js

# Driver receives the complete physical custody.
trip_fields = {f.get("fieldname") for f in trip["fields"]}
supplies = {
    "iftar_cartons", "iftar_bread_quantity", "iftar_carts", "iftar_tablecloths",
    "iftar_waste_bags", "iftar_gloves", "iftar_masks", "iftar_shoe_covers",
}
assert supplies.issubset(trip_fields)
for field in supplies:
    assert field in driver_py and field in driver_js
assert "خطة تحميل إفطار الصائم" in driver_py

# Site Manager sees inbound custody, distributes it and records the quality inspector later.
for token in ("عهدة السيارات الواردة", "تسليم المشرف حسب خطة مدير المشروع", "iftar_masks", "iftar_carts", "مفتش الجودة والتغذية", "متاح لاحقاً ولا يوقف التشغيل"):
    assert token in site_js
assert "Supervisor supplies exceed vehicle allocation" in team

# Supervisor receives detailed custody, owners/locations, signatures/photos and closeout.
report_fields = {f.get("fieldname") for f in report["fields"]}
assert {"carts", "masks", "bread_bags", "tablecloths", "gloves", "shoe_covers"}.issubset(report_fields)
for token in ("العهدة المستلمة", "صورة التسليم", "توقيع صاحب السفرة", "الفائض", "حفظ النعمة", "رفع السفر"):
    assert token in supervisor_js

# Final chain: Supervisor -> Site Manager -> assigned Project Manager -> Presidency.
assert "إرسال التقرير اليومي لمدير الموقع" in supervisor_js
assert "إرساله لمدير المشروع" in site_js
assert '_assigned(project, "project_manager_user")' in team
send_start = team.index("def send_authority_report")
send_section = team[send_start:send_start + 2500]
assert '"WAFD Project Manager"' in send_section
assert "اعتماد مدير المشروع وإرساله للرئاسة" in team_js

print("RC342 complete Iftar role model checks passed")
