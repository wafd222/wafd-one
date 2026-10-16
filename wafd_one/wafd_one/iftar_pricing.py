"""Pure pricing rules for WAFD Iftar Sa’im projects.

This module intentionally has no Frappe dependency so arithmetic can be regression-tested
without a live site/database. Prices are VAT-inclusive and expressed in SAR.
"""

STANDARD_MEAL = "الوجبة القياسية / Standard Iftar"
ZAMZAM_MEAL = "وجبة مع زمزم / Iftar + Zamzam"
CUSTOM_MEAL = "وجبة مخصصة / Custom Package"


def calculate_iftar_sale_price(base_price, paid_add_on_total=0, meal_template=None, include_zamzam=False):
    """Return base + selected paid add-ons + Zamzam package surcharge, rounded to halalas."""
    base = round(float(base_price or 0), 2)
    add_ons = round(float(paid_add_on_total or 0), 2)
    if base <= 0:
        raise ValueError("Base meal price must be greater than zero")
    zamzam = 1.50 if (meal_template == ZAMZAM_MEAL or bool(include_zamzam)) else 0.0
    return round(base + add_ons + zamzam + 1e-9, 2)


def calculate_vat_inclusive_totals(unit_price, quantity, vat_rate=15):
    """Return gross revenue, VAT included in gross, and net revenue in SAR."""
    gross = round(max(float(unit_price or 0), 0) * max(int(quantity or 0), 0), 2)
    rate = max(float(vat_rate or 0), 0)
    vat = round(gross * rate / (100 + rate), 2) if gross and rate else 0.0
    net = round(gross - vat, 2)
    return {"gross_revenue": gross, "vat_amount": vat, "net_revenue_excluding_vat": net}
