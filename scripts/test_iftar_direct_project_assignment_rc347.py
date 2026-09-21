"""Regression checks for RC347 direct and immediately refreshed project assignment."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
employee = (ROOT / "wafd_one/wafd_one/page/wafd_employee_team/wafd_employee_team.js").read_text()
team = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text()
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
patch = (ROOT / "wafd_one/wafd_one/patches/v10_0_0_rc347/execute.py").read_text()

# The management card must carry the exact project into Employee Management.
handler = team.split('$root.on("click.rc314", ".ift-open-employees"', 1)[1].split("});", 1)[0]
assert 'closest("[data-project]")' in handler
assert 'sessionStorage.setItem("wafd_iftar_assignment_project", project)' in handler
assert 'frappe.set_route("wafd-employee-team")' in handler

# Project assignment is visible before the long employee list and opens directly.
assert employee.index('id="wafd-iftar-project-list"') < employee.index('id="wafd-employee-list"')
assert 'sessionStorage.getItem("wafd_iftar_assignment_project")' in employee
assert 'setTimeout(() => openIftarAssignment(pending)' in employee
assert 'إكمال إسناد المشروع' in employee

# Changing or creating an employee immediately refreshes project-role candidates.
change_role = employee.split("function changeRole", 1)[1].split("function editAccount", 1)[0]
assert "loadIftarAssignments();" in change_role
create_employee = employee.split('$root.on("click", "#wafd-add-employee"', 1)[1]
assert "loadIftarAssignments();" in create_employee

# A submitted project cannot be saved without its two core assignees.
assignment = employee.split("function openIftarAssignment", 1)[1].split("function load()", 1)[0]
assert "if (!args.project_manager_user || !args.kitchen_supervisor_user)" in assignment

# Valid global managers are selectable, matching server validation.
team_options = portal.split("def _team_options():", 1)[1].split("@frappe.whitelist()", 1)[0]
assert "for management_role in GLOBAL_MANAGEMENT_ROLES" in team_options
assert "users.append(frappe.session.user)" in team_options

assert '"wafd_employee_team", "wafd_iftar_team"' in patch

print("RC347 direct Iftar project assignment and immediate option refresh checks passed")
