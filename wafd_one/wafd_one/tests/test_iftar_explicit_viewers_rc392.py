"""RC392 regression checks: Iftar viewer selection is explicit, not automatic."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TestExplicitIftarViewersRC392(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = (ROOT / 'iftar_stage_portal.py').read_text()
        cls.ui = (ROOT / 'page/wafd_employee_team/wafd_employee_team.js').read_text()
        cls.home = (ROOT / 'page/wafd_role_home/wafd_role_home.js').read_text()

    def test_only_registered_employees_in_viewer_options(self):
        block = self.backend.split('def _team_options():',1)[1].split('@frappe.whitelist()',1)[0]
        self.assertIn('if fieldname == "external_viewer_user":\n            users = list(all_employees)',block)
        self.assertIn('suffix = "" if fieldname == "external_viewer_user" or prepared',block)

    def test_only_explicit_selection_is_saved(self):
        block = self.backend.split('def save_project_team(',1)[1].split('# Kitchen stages',1)[0]
        self.assertIn('if external_viewer_users is not None:',block)
        self.assertIn('values["external_viewer_user"] = selected[0] if selected else ""',block)
        self.assertIn('frappe.db.delete("WAFD Iftar Viewer Assignment", {"project": project_name})',block)
        self.assertIn('for user in selected[1:]:',block)
        self.assertIn('prepare_task=True',block)
        self.assertIn('args.external_viewer_users',self.ui)

    def test_unselected_user_denied_card_and_api(self):
        self.assertIn('if (!response.message?.has_access)',self.home)
        self.assertIn('items = items.filter((item) => item.iftar_mode !== "viewer")',self.home)
        self.assertIn('assigned_names = _viewer_project_names(user)',self.backend)
        self.assertIn('filters["name"] = ["in", assigned_names] if assigned_names else "__none__"',self.backend)

    def test_operational_team_fields_still_present(self):
        for field in ('project_manager_user','kitchen_supervisor_user','site_manager_user'):
            self.assertIn('assignmentSelect("'+field+'"',self.ui)
