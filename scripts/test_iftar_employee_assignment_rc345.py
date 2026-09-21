"""Static regression checks for RC345 Iftar employee/project isolation."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
team_backend = (ROOT / "wafd_one/wafd_one/iftar_team.py").read_text()
employee = (ROOT / "wafd_one/wafd_one/page/wafd_employee_team/wafd_employee_team.js").read_text()
site = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_site/wafd_iftar_site.js").read_text()
team_page = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text()
project_meta = json.loads((ROOT / "wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json").read_text())

# Core employee roles and project assignment have one visible home.
assert "فريق مشاريع إفطار الصائم" in employee
assert "get_employee_project_assignments" in employee
assert "iftar_stage_portal.save_project_team" in employee
for fieldname in (
    "team_section", "project_manager_user", "kitchen_supervisor_user",
    "column_break_team", "delivery_supervisor_user", "site_manager_user", "external_viewer_user",
):
    field = next(item for item in project_meta["fields"] if item.get("fieldname") == fieldname)
    assert field.get("hidden") == 1, fieldname

# Project and site assignment no longer auto-grant employee roles.
assert "def _ensure_team_role" not in portal
assert "def assign_project_team_roles" not in team_backend
assert "Assign the employee task first in Employee Management" in portal
compat_assignment = team_backend.split("def assign_project_team(", 1)[1].split("@frappe.whitelist()", 1)[0]
assert '_require("System Manager", "WAFD Operations Manager")' in compat_assignment
assert '"WAFD Project Manager"' not in compat_assignment

# Travel-supervisor selection is limited to accounts prepared in Employee Management.
supervisor_options = portal.split("def get_supervisor_user_options():", 1)[1].split("@frappe.whitelist()", 1)[0]
assert 'filters={"role": SUPERVISOR_ROLE, "parenttype": "User"}' in supervisor_options
quick_setup = portal.split("def save_quick_supervisor_setup", 1)[1]
assert "Assign the Iftar Travel Supervisor task in Employee Management first" in quick_setup

# Only the Project Manager owns supervisor/assistant/table-owner planning.
assert "openProjectSetupDialog" in team_page
assert "openSetup" not in site
assert "ifs-quick-sup" not in site

# RC345 remains scoped to the dedicated Iftar flow and Employee Management.
changed_scope = {
    "wafd_one/employee_team.py",
    "wafd_one/wafd_one/iftar_stage_portal.py",
    "wafd_one/wafd_one/iftar_team.py",
    "wafd_one/wafd_one/doctype/wafd_iftar_project/wafd_iftar_project.json",
    "wafd_one/wafd_one/page/wafd_employee_team/wafd_employee_team.js",
    "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js",
    "wafd_one/wafd_one/page/wafd_iftar_site/wafd_iftar_site.js",
}
for forbidden in ("undertaking", "quotation", "inventory", "finance", "cleaning", "driver_portal", "delivery_tracking"):
    assert not any(forbidden in path for path in changed_scope)

print("RC345 Iftar employee-management assignment and isolation checks passed")
