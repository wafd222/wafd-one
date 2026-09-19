"""Regression checks for RC331 orphan Supervisor assignments."""

from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "wafd_one" / "wafd_one" / "iftar_stage_portal.py"
PATCH = ROOT / "wafd_one" / "wafd_one" / "patches" / "v10_0_0_rc331" / "execute.py"


class Missing(Exception):
    pass


def doc(**values):
    return types.SimpleNamespace(**values)


project = doc(
    name="WAFD-IFTAR-VALID",
    project_title="المسجد النبوي الشريف",
    distribution_site="التوسعة الشرقية",
    contracting_entity="شؤون الحرمين",
)
operation = doc(site_receipt_approved=1)
report = doc(
    name="REPORT-VALID",
    project=project.name,
    daily_operation="OP-VALID",
    operation_date="2026-09-19",
    supervisor_name="مشرف الاختبار",
    planned_meals=500,
    cartons=20,
    received_meals=500,
    received_at=None,
    report_submitted=0,
    manager_approved=0,
    table_owners=[],
    assistants_attendance=[],
)
valid_plan = doc(
    name="PLAN-VALID",
    project=project.name,
    supervisor_name="مشرف الاختبار",
    assigned_meals=500,
    table_owners_count=1,
)
orphan_plan = doc(
    name="PLAN-ORPHAN",
    project="WAFD-IFTAR-00024",
    supervisor_name="قديم",
    assigned_meals=500,
    table_owners_count=1,
)


class PortalDB:
    def get_value(self, doctype, name, fields, as_dict=False):
        refs = {
            "REPORT-ORPHAN": doc(project="WAFD-IFTAR-00024", daily_operation="OP-ORPHAN"),
            "REPORT-VALID": doc(project=project.name, daily_operation="OP-VALID"),
        }
        return refs.get(name)

    def exists(self, doctype, name):
        existing = {
            ("WAFD Iftar Project", project.name),
            ("WAFD Iftar Daily Operation", "OP-VALID"),
        }
        return (doctype, name) in existing


frappe = types.SimpleNamespace()
frappe.session = doc(user="supervisor@example.com")
frappe.db = PortalDB()
frappe.DoesNotExistError = Missing
frappe.utils = types.SimpleNamespace(get_fullname=lambda user: "مشرف الاختبار")
frappe.whitelist = lambda: (lambda fn: fn)
frappe.get_all = lambda doctype, **kwargs: (
    ["REPORT-ORPHAN", "REPORT-VALID"]
    if doctype == "WAFD Iftar Supervisor Daily Report"
    else ["PLAN-ORPHAN", "PLAN-VALID"]
)
frappe.get_doc = lambda doctype, name: {
    ("WAFD Iftar Supervisor Daily Report", "REPORT-VALID"): report,
    ("WAFD Iftar Project", project.name): project,
    ("WAFD Iftar Daily Operation", "OP-VALID"): operation,
    ("WAFD Iftar Supervisor Plan", "PLAN-ORPHAN"): orphan_plan,
    ("WAFD Iftar Supervisor Plan", "PLAN-VALID"): valid_plan,
}[(doctype, name)]
frappe.throw = lambda message, *args: (_ for _ in ()).throw(RuntimeError(message))
frappe.PermissionError = PermissionError

tree = ast.parse(PORTAL.read_text())
selected = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name in {"_supervisor_report_payload", "get_supervisor_portal_data"}
]
module = ast.Module(body=selected, type_ignores=[])
namespace = {
    "frappe": frappe,
    "_": lambda value: value,
    "cint": lambda value: int(value or 0),
    "_roles": lambda: {"WAFD Iftar Supervisor"},
    "_is_global_manager": lambda roles=None: False,
}
exec(compile(module, str(PORTAL), "exec"), namespace)
payload = namespace["get_supervisor_portal_data"]()

assert [row["name"] for row in payload["reports"]] == ["REPORT-VALID"]
assert [row["name"] for row in payload["plans"]] == ["PLAN-VALID"]
assert payload["stale_assignments_skipped"] == 2


class CleanupDB:
    def __init__(self):
        self.deleted = []

    def exists(self, doctype, name):
        return name == project.name

    def table_exists(self, doctype):
        return True

    def delete(self, doctype, filters):
        self.deleted.append((doctype, filters))


cleanup = types.ModuleType("frappe")
cleanup.db = CleanupDB()
cleanup.get_all = lambda doctype, **kwargs: (
    [doc(name="REPORT-ORPHAN", project="WAFD-IFTAR-00024"), doc(name="REPORT-VALID", project=project.name)]
    if doctype == "WAFD Iftar Supervisor Daily Report"
    else [doc(name="PLAN-ORPHAN", project="WAFD-IFTAR-00024"), doc(name="PLAN-VALID", project=project.name)]
)
cleanup.clear_cache = lambda: None
sys.modules["frappe"] = cleanup
spec = importlib.util.spec_from_file_location("rc331_cleanup", PATCH)
patch_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(patch_module)
patch_module.execute()

parent_deletes = [item for item in cleanup.db.deleted if item[0] in {
    "WAFD Iftar Supervisor Daily Report", "WAFD Iftar Supervisor Plan"
}]
assert parent_deletes == [
    ("WAFD Iftar Supervisor Daily Report", {"name": ["in", ["REPORT-ORPHAN"]]}),
    ("WAFD Iftar Supervisor Plan", {"name": ["in", ["PLAN-ORPHAN"]]}),
]

print("RC331 orphan assignment filtering and cleanup passed")
