"""RC391: preserve role boundaries while enabling many project-scoped viewers."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestIftarMultiViewerRC391(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = (ROOT / "iftar_stage_portal.py").read_text()
        cls.ui = (ROOT / "page/wafd_employee_team/wafd_employee_team.js").read_text()

    def test_separate_viewer_assignment_doctype(self):
        path = ROOT / "doctype/wafd_iftar_viewer_assignment/wafd_iftar_viewer_assignment.json"
        meta = json.loads(path.read_text())
        self.assertEqual(meta["name"], "WAFD Iftar Viewer Assignment")
        self.assertEqual({x["fieldname"] for x in meta["fields"]}, {"project", "viewer_user"})
        self.assertNotIn("WAFD Iftar Authority Viewer", [p["role"] for p in meta["permissions"]])

    def test_all_viewer_entry_points_use_project_membership(self):
        for func in ("_project_access", "_get_authority_final_report_html"):
            part = self.backend[self.backend.index("def " + func):]
            self.assertIn("_is_iftar_viewer(project, user)", part[:5500])
        for func in ("has_iftar_viewer_access", "get_authority_monitoring_data"):
            part = self.backend[self.backend.index("def " + func):]
            self.assertIn("_viewer_project_names(user)", part[:3500])

    def test_old_assignment_preserved_and_new_list_optional(self):
        part = self.backend[self.backend.index("def save_project_team"):self.backend.index("# Kitchen stages")]
        self.assertIn("external_viewer_users=None", part)
        self.assertIn("if external_viewer_users is not None:", part)
        self.assertIn('values["external_viewer_user"] = selected[0] if selected else ""', part)
        self.assertIn('for user in selected[1:]:', part)
        self.assertIn('_validate_team_user("external_viewer_user", item, prepare_task=True)', part)

    def test_ui_multi_select_and_existing_project_team_unchanged(self):
        self.assertIn('class="wafd-iftar-viewer-choice"', self.ui)
        self.assertIn('args.external_viewer_users =', self.ui)
        self.assertIn('assignmentSelect("project_manager_user"', self.ui)
        self.assertIn('assignmentSelect("kitchen_supervisor_user"', self.ui)
        self.assertIn('assignmentSelect("site_manager_user"', self.ui)
