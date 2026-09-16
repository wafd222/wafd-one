"""Static checks for RC309 simplified Iftar workflow."""
from pathlib import Path
import ast
import tomllib

ROOT = Path(__file__).resolve().parents[1]

def require(path, needles):
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path}: missing {missing}")
    return text

project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
assert project["project"]["version"] == "10.0.0rc309"

team = require("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js", [
    "إدارة المشروع والمهام",
    "اعتماد المشروع وإظهار المهام للموظفين",
    "ift-stage-strip",
    "اعتماد مرحلة المطبخ",
    "المشرفون وأصحاب السفر",
    "بانتظار المرحلة السابقة",
])
assert '<select class="form-control ift-project"' not in team, "Project selector should not return to the simplified role screen"

pro = require("wafd_one/wafd_one/iftar_pro.py", [
    'return {"name": doc.name, "route": f"/app/wafd-iftar-project/{doc.name}", "draft": 1}',
])
create_block = pro[pro.index("def create_project(data):"):pro.index("def _copy_supervisor_plans", pro.index("def create_project(data):"))]
assert "doc.submit()" not in create_block
assert "generate_daily_operations(doc.name" not in create_block

backend = require("wafd_one/wafd_one/iftar_team.py", [
    "def approve_project_plan(project_name):",
    "أضف المشرفين وأصحاب السفر من شاشة الإدارة قبل اعتماد المشروع",
    "project.submit()",
    "generate_daily_operations(project.name",
    '"kitchen_started": 1',
    "def approve_delivery_dispatch(operation_name):",
    "def approve_site_receipt(operation_name, received_meals):",
])
ast.parse(backend)

require("wafd_one/wafd_one/page/wafd_iftar_operations/wafd_iftar_operations.js", [
    'frappe.set_route("wafd-iftar-team")',
])
daily = require("wafd_one/wafd_one/doctype/wafd_iftar_daily_operation/wafd_iftar_daily_operation.js", [
    "فتح شاشة مهمتي",
    'frappe.set_route("wafd-iftar-team")',
])
for legacy_action in ("اعتماد الإنتاج", "اعتماد التغليف", "اعتماد التحميل", "اعتماد استلام الموقع"):
    assert legacy_action not in daily, f"Raw form still exposes stage action: {legacy_action}"

require("wafd_one/patches.txt", ["wafd_one.wafd_one.patches.v10_0_0_rc309.execute"] )
print("RC309 simplified Iftar workflow checks passed")
