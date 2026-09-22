"""Static regression checks for RC351 permanent project staffing and handover."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
team = (ROOT / "wafd_one/wafd_one/iftar_team.py").read_text()
employee = (ROOT / "wafd_one/wafd_one/page/wafd_employee_team/wafd_employee_team.js").read_text()
site = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_site/wafd_iftar_site.js").read_text()
supervisor = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_supervisor/wafd_iftar_supervisor.js").read_text()
patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc351/execute.py").read_text()

# Every managed employee is visible while only the selected narrow task is added.
assert "def _managed_employee_users():" in portal
assert 'users.extend(all_employees)' in portal
assert "def _prepare_employee_for_iftar_task" in portal
assert "account.add_roles(required_role)" in portal
assert "prepare_task=True" in portal
assert "users.extend(_managed_employee_users())" in portal

# The team is project-long and copied to daily reports after site receipt.
assert "هذا الفريق ثابت طوال مدة المشروع" in employee
receipt = team.split("def approve_site_receipt", 1)[1].split("@frappe.whitelist()", 1)[0]
assert "ensure_supervisor_reports(operation.name)" in receipt
assert '"setup_required": True' in receipt
assert "wafd_iftar_supervisor_task_ready" in team
assert "wafd_iftar_site_delivery_arrived" in team
assert "استلام الوجبات وتجهيز مهام المشرفين" in site
assert "const auto=(reportField,tripField)" in site
assert "أنت مسند طوال مدة المشروع" in supervisor
assert "wafd_iftar_site_delivery_arrived" in site
assert "wafd_iftar_supervisor_task_ready" in supervisor

# The patch refreshes only Iftar/Employee Management pages.
for expected in ("wafd_employee_team", "wafd_iftar_team", "wafd_iftar_site", "wafd_iftar_supervisor"):
    assert expected in patch
for forbidden in ("undertaking", "quotation", "finance", "inventory", "cleaning"):
    assert forbidden not in patch

print("RC351 permanent Iftar staffing and fast handover checks passed")
