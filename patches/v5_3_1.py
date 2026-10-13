import frappe


def execute():
    """Recalculate invoice/payment balances after finance integrity protections."""
    if not frappe.db.table_exists("WAFD Invoice"):
        return
    from wafd_one.finance import refresh_invoice_and_project

    for invoice_name in frappe.get_all("WAFD Invoice", pluck="name"):
        refresh_invoice_and_project(invoice_name)
