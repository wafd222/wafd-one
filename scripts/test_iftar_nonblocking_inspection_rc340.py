from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
team = (ROOT / "wafd_one/wafd_one/iftar_team.py").read_text()
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
pro = (ROOT / "wafd_one/wafd_one/iftar_pro.py").read_text()
operation = (ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_daily_operation/wafd_iftar_daily_operation.py").read_text()
form_js = (ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_daily_operation/wafd_iftar_daily_operation.js").read_text()
site_js = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_site/wafd_iftar_site.js").read_text()
template = (ROOT / "wafd_one/templates/print_formats/wafd_iftar_official_daily_report.html").read_text()

assert "if not cint(operation.site_receipt_approved):" in team
assert "Authority inspection is required before supervisor assignments" not in team
assert "Authority inspection is required before supervisor handover" not in team
assert "Record the food inspector approval and signature before final dispatch" in team
assert 'operation.get("site_receipt_approved")' in portal
assert 'operation.get("authority_inspection_approved")' not in portal
assert "stage == \"delivered\" and not cint(doc.authority_inspection_approved)" not in pro
assert "if delivered and not cint(self.authority_inspection_approved)" not in operation
assert 'addStageAction(__("فحص مشرف التغذية")' not in form_js
assert "تسجيل موافقة وتوقيع مفتش التغذية" in site_js
assert "متاح لاحقاً ولا يوقف التشغيل" in site_js
assert "o.site_receipt_approved&&(p.supervisor_plans||[]).length" in site_js
assert '<div class="footer">' not in template

print("RC340 non-blocking authority inspection and PDF page checks passed")
