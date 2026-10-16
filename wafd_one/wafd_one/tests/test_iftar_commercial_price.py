"""Focused regression tests for Iftar commercial price arithmetic."""
import unittest

from wafd_one.wafd_one.iftar_pricing import calculate_iftar_sale_price, calculate_vat_inclusive_totals

STANDARD = "الوجبة القياسية / Standard Iftar"
ZAMZAM = "وجبة مع زمزم / Iftar + Zamzam"
CUSTOM = "وجبة مخصصة / Custom Package"


class TestIftarCommercialPrice(unittest.TestCase):
    def test_default_standard_price(self):
        self.assertEqual(calculate_iftar_sale_price(9, 0, STANDARD), 9.0)

    def test_custom_base_is_preserved_when_returning_to_standard(self):
        self.assertEqual(calculate_iftar_sale_price(7, 0, STANDARD), 7.0)

    def test_zamzam_adds_surcharge_without_mutating_base(self):
        self.assertEqual(calculate_iftar_sale_price(7, 0, ZAMZAM), 8.5)
        self.assertEqual(calculate_iftar_sale_price(7, 0, STANDARD), 7.0)

    def test_paid_addon_is_added_to_base(self):
        self.assertEqual(calculate_iftar_sale_price(9, 1.2, STANDARD), 10.2)

    def test_zamzam_and_paid_addon_are_added_once(self):
        self.assertEqual(calculate_iftar_sale_price(7, 1.2, ZAMZAM), 9.7)

    def test_zamzam_toggle_also_adds_surcharge_to_standard_package(self):
        self.assertEqual(calculate_iftar_sale_price(7, 0, STANDARD, include_zamzam=True), 8.5)
        self.assertEqual(calculate_iftar_sale_price(7, 0, STANDARD, include_zamzam=False), 7.0)

    def test_custom_package_does_not_get_zamzam_surcharge_implicitly(self):
        self.assertEqual(calculate_iftar_sale_price(7, 1.2, CUSTOM), 8.2)

    def test_vat_inclusive_revenue_matches_project_summary_examples(self):
        self.assertEqual(calculate_vat_inclusive_totals(8.5, 300), {
            "gross_revenue": 2550.0, "vat_amount": 332.61, "net_revenue_excluding_vat": 2217.39
        })
        self.assertEqual(calculate_vat_inclusive_totals(9, 500), {
            "gross_revenue": 4500.0, "vat_amount": 586.96, "net_revenue_excluding_vat": 3913.04
        })

    def test_nonpositive_base_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_iftar_sale_price(0, 0, STANDARD)


if __name__ == "__main__":
    unittest.main()
