"""Static contract checks for Iftar workflow boundaries and role UI."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestIftarWorkflowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.portal = (ROOT / "iftar_stage_portal.py").read_text()
        cls.team_backend = (ROOT / "iftar_team.py").read_text()
        cls.team_ui = (ROOT / "page/wafd_iftar_team/wafd_iftar_team.js").read_text()
        cls.viewer_ui = (ROOT / "page/wafd_iftar_authority_viewer/wafd_iftar_authority_viewer.js").read_text()
        cls.wizard_ui = (ROOT / "page/wafd_iftar_wizard/wafd_iftar_wizard.js").read_text()

    def test_kitchen_stages_are_ordered(self):
        start = self.portal.index("def approve_kitchen_stage")
        section = self.portal[start:start + 7000]
        self.assertIn('stage not in ("production", "packaging", "loading")', section)
        self.assertIn('if stage == "production"', section)
        self.assertIn('elif stage == "packaging"', section)
        self.assertIn('if stage == "loading":', section)
        self.assertIn('اعتمد التغليف أولاً', section)

    def test_supervisor_report_requires_quantity_reconciliation(self):
        start = self.team_backend.index("def submit_supervisor_report")
        section = self.team_backend[start:start + 4500]
        self.assertIn("owner_delivered != cint(report.received_meals)", section)
        self.assertIn("sum(values) != cint(report.received_meals)", section)

    def test_external_viewer_is_project_scoped_and_read_only(self):
        start = self.portal.index("def get_authority_monitoring_data")
        section = self.portal[start:start + 2500]
        self.assertIn('filters["external_viewer_user"] = user', section)
        self.assertIn('filters["docstatus"] = 1', section)
        self.assertIn("EXTERNAL_VIEWER_ROLE", section)

    def test_authority_ui_displays_supervisor_evidence(self):
        self.assertIn("o.supervisor_evidence", self.viewer_ui)
        self.assertIn("ev.photo", self.viewer_ui)

    def test_manager_card_does_not_offer_duplicate_legacy_portal_shortcut(self):
        self.assertNotIn("فتح إدارة إفطار الصائم", self.team_ui)

    def test_wizard_keeps_base_price_separate_from_final_price(self):
        self.assertIn("out.standard_meal_price = Number(state.baseSalePrice", self.wizard_ui)
        self.assertIn("out.sale_price_per_meal = currentFinalSalePrice()", self.wizard_ui)
        self.assertIn("const base = Math.max(0, Number(state.baseSalePrice", self.wizard_ui)

    def test_legacy_zero_base_price_has_safe_default(self):
        project = (ROOT / "doctype/wafd_iftar_project/wafd_iftar_project.py").read_text()
        self.assertIn("if base_price == 0:", project)
        self.assertIn("base_price = 9.0", project)


    def test_reused_roster_keeps_user_assignments_and_resets_incompatible_quantities(self):
        creator = (ROOT / "iftar_pro.py").read_text()
        start = creator.index("def _copy_supervisor_plans")
        section = creator[start:creator.index("@frappe.whitelist()", start)]
        self.assertIn("dst.supervisor_user = src.supervisor_user", section)
        self.assertIn("reuse_quantities = bool(source_total and source_total == cint(target.daily_meals))", section)
        self.assertIn("cint(row.meal_quantity) if reuse_quantities else 0", section)
        self.assertIn("\"active\": row.active", section)

    def test_site_receipt_dialog_does_not_claim_tasks_are_created(self):
        site_ui = (ROOT / "page/wafd_iftar_site/wafd_iftar_site.js").read_text()
        self.assertIn("title:'تأكيد استلام الوجبات'", site_ui)
        self.assertIn("primary_action_label:'تأكيد الاستلام'", site_ui)
        self.assertIn("قبل تجهيز مهام المشرفين وتوزيع الوجبات", site_ui)

    def test_authority_inspection_is_mandatory_before_supervisor_distribution(self):
        start = self.team_backend.index("def ensure_supervisor_reports")
        section = self.team_backend[start:start + 1800]
        self.assertIn("if not cint(operation.authority_inspection_approved):", section)
        self.assertIn("Authority inspection photo and signature approval is required", section)
        start = self.team_backend.index("def receive_for_supervisor")
        section = self.team_backend[start:start + 1200]
        self.assertIn("if not cint(operation.authority_inspection_approved):", section)

    def test_site_receipt_does_not_create_supervisor_tasks_before_inspection(self):
        start = self.team_backend.index("def approve_site_receipt")
        section = self.team_backend[start:self.team_backend.index("def approve_authority_inspection", start)]
        self.assertNotIn("ensure_supervisor_reports(operation.name)", section)
        self.assertIn('"inspection_required": True', section)

    def test_site_ui_describes_inspection_as_mandatory_gate(self):
        site_ui = (ROOT / "page/wafd_iftar_site/wafd_iftar_site.js").read_text()
        self.assertIn("مطلوب قبل توزيع الوجبات على المشرفين", site_ui)
        self.assertIn("o.site_receipt_approved&&o.authority_inspection_approved", site_ui)

    def test_standard_selection_resets_zamzam_and_optional_addons(self):
        self.assertIn("if(meal==='الوجبة القياسية / Standard Iftar')", self.wizard_ui)
        reset_block = self.wizard_ui.split("if(meal==='الوجبة القياسية / Standard Iftar')", 1)[1][:220]
        self.assertIn("set('include_zamzam',0)", reset_block)
        self.assertIn("prop('checked', false)", reset_block)

    def test_create_project_keeps_base_and_final_price_separate_on_server(self):
        creator = (ROOT / "iftar_pro.py").read_text()
        self.assertIn('data["standard_meal_price"] = base_price', creator)
        self.assertIn('data["sale_price_per_meal"] = frappe.utils.flt(entered_sale_price, precision=2)', creator)

    def test_manager_portal_does_not_duplicate_trip_details_in_project_card(self):
        # Trip details remain in operational stages; the summary card only shows the current stage.
        manager_block = self.team_ui.split("function projectCard", 1)[1].split("function", 1)[0] if "function projectCard" in self.team_ui else self.team_ui
        self.assertNotIn("tripRows(p.current_operation.trips)", manager_block)


if __name__ == "__main__":
    unittest.main()
