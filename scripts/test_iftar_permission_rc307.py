"""Regression checks for RC307 Iftar controller permissions."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECURITY = ROOT / "wafd_one" / "wafd_one" / "iftar_security.py"


class FakeDB:
    def escape(self, value):
        return repr(value)

    def exists(self, doctype, filters):
        return filters.get("supervisor_user") == "field@example.com"


roles_by_user = {
    "Administrator": {"System Manager"},
    "ops@example.com": {"WAFD Operations Manager"},
    "pm@example.com": {"WAFD Project Manager"},
    "kitchen@example.com": {"WAFD Iftar Kitchen Supervisor"},
    "field@example.com": {"WAFD Iftar Supervisor"},
}

frappe = types.ModuleType("frappe")
frappe.session = types.SimpleNamespace(user="pm@example.com")
frappe.db = FakeDB()
frappe.get_roles = lambda user=None: list(roles_by_user.get(user or frappe.session.user, set()))

project = types.SimpleNamespace(
    name="IFTAR-0001",
    project_manager_user="pm@example.com",
    kitchen_supervisor_user="kitchen@example.com",
    delivery_supervisor_user="delivery@example.com",
    site_manager_user="site@example.com",
)
frappe.get_doc = lambda doctype, name: project
sys.modules["frappe"] = frappe

spec = importlib.util.spec_from_file_location("iftar_security_rc307", SECURITY)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

new_project = types.SimpleNamespace(
    __islocal=True,
    name=None,
    project_manager_user=None,
    kitchen_supervisor_user=None,
    delivery_supervisor_user=None,
    site_manager_user=None,
)

# Management and project managers can create; operational staff cannot.
assert module.project_has_permission(new_project, "Administrator", ptype="create") is True
assert module.project_has_permission(new_project, "ops@example.com", permission_type="create") is True
assert module.project_has_permission(new_project, "pm@example.com", permission_type="create") is True
assert module.project_has_permission(new_project, "kitchen@example.com", permission_type="create") is False

# Assigned employees and field supervisors can access an existing project.
assert module.project_has_permission(project, "kitchen@example.com", permission_type="read") is True
assert module.project_has_permission(project, "field@example.com", permission_type="read") is True

# Management must receive explicit True on every protected Iftar document.
child = types.SimpleNamespace(project=project.name, supervisor_user="field@example.com")
assert module.daily_has_permission(child, "ops@example.com", permission_type="create") is True
assert module.plan_has_permission(child, "ops@example.com", permission_type="write") is True
assert module.report_has_permission(child, "ops@example.com", permission_type="submit") is True

print("RC307 Iftar controller permission checks passed")
