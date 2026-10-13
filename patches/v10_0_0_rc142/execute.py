from __future__ import annotations

import re
import frappe
from frappe.utils import flt, cint


def _clean(value):
    return re.sub(r"<[^>]*>", " ", value or "").replace("  ", " ").strip()


def execute():
    """Repair legacy Iftar cached totals and HTML-contaminated project labels."""
    rows = frappe.get_all(
        "WAFD Iftar Project",
        fields=["name", "project_title", "sale_price_per_meal", "total_meals", "total_project_cost"],
        limit_page_length=0,
    )
    for row in rows:
        price = flt(row.sale_price_per_meal, 2)
        meals = cint(row.total_meals)
        gross = flt(price * meals, 2)
        vat = flt(gross * 15 / 115, 2)
        net = flt(gross - vat, 2)
        cost = flt(row.total_project_cost, 2)
        values = {
            "total_revenue": gross,
            "vat_amount": vat,
            "net_revenue_excluding_vat": net,
            "expected_profit": flt(net - cost, 2),
        }
        cleaned = _clean(row.project_title)
        if cleaned and cleaned != (row.project_title or ""):
            values["project_title"] = cleaned
        frappe.db.set_value("WAFD Iftar Project", row.name, values, update_modified=False)
