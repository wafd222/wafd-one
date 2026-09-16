"""Static regression checks for RC310 Iftar employee task publishing."""
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
assert project["project"]["version"] == "10.0.0rc310"

backend = require("wafd_one/wafd_one/iftar_team.py", [
    "def _assignment_duties(project, user=None):",
    "def _visible_project_rows(roles, project_name=None):",
    "def get_my_iftar_task_summary(date=None):",
    'mode = "multi"',
    'operation["my_duties"]',
    '"wafd_iftar_task_published"',
    '"published_count": len(published_users)',
])
ast.parse(backend)
assert 'elif roles & {"WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor"}' not in backend[backend.index('def _visible_project_rows'):backend.index('def _fallback_mode_from_roles')]

team_js = require("wafd_one/wafd_one/page/wafd_iftar_team/wafd_iftar_team.js", [
    "function multiView()",
    'multi: "مهامي في إفطار الصائم"',
    "تم إسناد مهمة التوصيل لك",
    "تم إسناد مهمة الموقع لك",
    "published_count",
])

home_js = require("wafd_one/wafd_one/page/wafd_role_home/wafd_role_home.js", [
    "async function refreshIftarAssignmentCard()",
    "get_my_iftar_task_summary",
    "مهمة إفطار الصائم اليوم",
    "wafd_iftar_task_published",
])

patch = require("wafd_one/wafd_one/patches/v10_0_0_rc310/execute.py", [
    "CORE_ROLE_BY_FIELD",
    "generate_daily_operations",
    '"WAFD Iftar Supervisor"',
])
ast.parse(patch)
require("wafd_one/patches.txt", ["wafd_one.wafd_one.patches.v10_0_0_rc310.execute"])
print("RC310 Iftar task publishing checks passed")
