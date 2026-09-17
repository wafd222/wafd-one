"""Static release checks for RC314 Iftar staged workflow."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text(encoding="utf-8")
page = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text(encoding="utf-8")
role_home = (ROOT / "wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js").read_text(encoding="utf-8")
project = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json").read_text(encoding="utf-8"))
daily = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_daily_operation/wafd_iftar_daily_operation.json").read_text(encoding="utf-8"))

for symbol in ["approve_kitchen_stage", "approve_delivery_plan", "get_portal_data", "save_project_team"]:
    assert f"def {symbol}" in portal, symbol
for stage in ['"production"', '"packaging"', '"loading"']:
    assert stage in portal, stage
for phrase in ["اعتماد الإنتاج", "اعتماد التغليف", "اعتماد التحميل", "توزيع الوجبات على السيارات", "متابعة للقراءة فقط"]:
    assert phrase in page, phrase
for phrase in ["مهمة إفطار الصائم", "مهام إفطار الصائم", "متابعة إفطار الصائم"]:
    assert phrase in role_home, phrase
assert any(f.get("fieldname") == "external_viewer_user" for f in project["fields"])
for field in ["production_approved_by", "packaging_approved_by", "loading_approved_by", "workflow_notes"]:
    assert any(f.get("fieldname") == field for f in daily["fields"]), field

# The RC314 portal creates linked Iftar trips but must not patch delivery source files.
assert 'from wafd_one.delivery_supervisor import _ensure_delivery_location' in portal
assert '"iftar_daily_operation": operation.name' in portal

print("RC314 Iftar staged workflow static checks: OK")
