"""Regression checks for RC346 draft isolation and Kitchen task publishing."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
pro = (ROOT / "wafd_one/wafd_one/iftar_pro.py").read_text()
project_controller = (ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.py").read_text()
project_js = (ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.js").read_text()
operation_js = (ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_daily_operation/wafd_iftar_daily_operation.js").read_text()
wizard = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_wizard/wafd_iftar_wizard.js").read_text()
employee = (ROOT / "wafd_one/wafd_one/page/wafd_employee_team/wafd_employee_team.js").read_text()
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc346/execute.py").read_text()

# Creation produces administration data only; it does not publish operational days.
create_section = pro.split("def create_project(data):", 1)[1].split("def _copy_supervisor_plans", 1)[0]
assert "generate_daily_operations(doc.name" not in create_section
assert '"requires_team_assignment": 1' in create_section
assert '"route": f"/app/wafd-employee-team"' in create_section

# No API or controller hook may create employee tasks for a draft.
generate_section = pro.split("def generate_daily_operations", 1)[1].split("def get_project_operations", 1)[0]
assert "if cint(project.docstatus) != 1:" in generate_section
after_insert = project_controller.split("def after_insert", 1)[1].split("def on_update", 1)[0]
draft_update = project_controller.split("def on_update", 1)[1].split("def on_submit", 1)[0]
assert "_sync_daily_operations" not in after_insert
assert "_sync_daily_operations" not in draft_update

# Wizard opens the one assignment location; Employee Management publishes after assignment.
assert "wafd_iftar_assignment_project" in wizard
assert "frappe.set_route('wafd-employee-team')" in wizard
assert "WAFD Iftar Daily Operation" not in wizard.split("createButton.addEventListener", 1)[1]
assert "approve_project_plan" in employee
assert "Select the Project Manager and Kitchen Supervisor before approval" in employee
assert '"docstatus", "project_title"' in portal

# Classic forms cannot execute the role workflow or create a second team plan.
for forbidden in ("اعتماد الإنتاج", "اعتماد التغليف", "اعتماد التحميل", "اعتماد التسليم", "اعتماد الاستلام"):
    assert forbidden not in operation_js
assert "خطط المشرفين والفرق" not in project_js
assert "إضافة خطة مشرف" not in project_js
assert "توليد الأيام الناقصة" not in project_js

# Upgrade removes only untouched auto-generated draft rows and preserves activity/history.
assert "_remove_untouched_draft_operations" in patch
assert "ACTIVITY_FIELDS" in patch
assert 'frappe.db.exists("WAFD Delivery Trip"' in patch
assert 'frappe.db.exists("WAFD Iftar Supervisor Daily Report"' in patch

print("RC346 draft isolation and post-approval Kitchen publishing checks passed")
