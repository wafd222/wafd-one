import frappe


def execute():
    """Recalculate persisted invoice/payment balances after the finance safeguards upgrade."""
    from wafd_one.finance import refresh_invoice_and_project, refresh_project_financials

    for invoice_name in frappe.get_all("WAFD Invoice", pluck="name"):
        refresh_invoice_and_project(invoice_name)

    for project_name in frappe.get_all("WAFD Catering Project", pluck="name"):
        refresh_project_financials(project_name)
