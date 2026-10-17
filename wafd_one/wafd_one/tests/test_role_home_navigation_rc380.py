from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TestRoleHomeNavigationRC380(unittest.TestCase):
    def test_mobile_cards_use_delegated_click_handler(self):
        source = (ROOT / "page" / "wafd_role_home" / "wafd_role_home.js").read_text(encoding="utf-8")
        self.assertIn('off("click.wafdMobileCard", ".wafd-mobile-card").on("click.wafdMobileCard", ".wafd-mobile-card"', source)

    def test_role_home_restores_interactivity_after_return(self):
        source = (ROOT / "page" / "wafd_role_home" / "wafd_role_home.js").read_text(encoding="utf-8")
        self.assertIn("function wafdRestoreRoleHomeInteractivity()", source)
        self.assertIn('window.addEventListener("pageshow"', source)
        self.assertIn('window.addEventListener("focus"', source)
        self.assertIn('frappe.pages["wafd-role-home"].on_page_show', source)
        self.assertIn("frappe.dom.unfreeze()", source)

if __name__ == "__main__":
    unittest.main()
