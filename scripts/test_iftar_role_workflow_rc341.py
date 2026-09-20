from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
portal = (ROOT / "wafd_one/wafd_one/iftar_stage_portal.py").read_text()
team = (ROOT / "wafd_one/wafd_one/iftar_team.py").read_text()
team_js = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js").read_text()
site_js = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_site/wafd_iftar_site.js").read_text()
supervisor_js = (ROOT / "wafd_one/wafd_one/page/wafd_iftar_supervisor/wafd_iftar_supervisor.js").read_text()

# Approved-only visibility for employee screens.
assert '"name", "docstatus", "project_title"' in portal
assert '("management" in duties or cint(row.docstatus) == 1)' in portal

# Kitchen owns production, packaging, loading and allocation to vehicles.
assert 'if not cint(op.get("delivery_plan_approved"))' in portal
assert 'mode in {"kitchen", "delivery"}' in portal
assert '{"kitchen", "delivery"} & duties' in portal
assert "توزيع الوجبات المحملة على السيارات" in team_js
assert 'x.task?.name === operationName' in team_js

# Administration approval precedes detailed field-team planning.
assert 'required_at_start = ("project_manager_user", "kitchen_supervisor_user")' in team
assert "if not plans:" not in team[team.index("def approve_project_plan"):team.index("def _submitted_operation")]

# Project Manager owns the nested supervisor / assistant / table-owner setup.
assert 'response["supervisor_options"]' in portal
assert 'row["supervisor_plans"]' in portal
assert '"management" not in duties and "project_manager" not in duties' in portal
assert "المشرفون والمساعدون" in team_js
assert "أصحاب السفر وتوزيع الوجبات" in team_js
assert "رقم جوال المشرف" in team_js
assert "po-meals" in team_js and "po-bread" in team_js and "po-tables" in team_js
assert "ifs-setup-supervisors" not in site_js

# Supervisor screen receives the complete allocation including cartons.
assert '"planned_cartons"' in portal
assert "planned_cartons" in supervisor_js
assert "اطلب من مدير المشروع" in supervisor_js

print("RC341 role workflow and project-manager assignment checks passed")
