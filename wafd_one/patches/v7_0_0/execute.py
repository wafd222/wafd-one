import frappe


def execute():
    from wafd_one.finance import refresh_invoice_and_project, refresh_project_financials

    for invoice in frappe.get_all("WAFD Invoice", pluck="name"):
        refresh_invoice_and_project(invoice)
    for project in frappe.get_all("WAFD Catering Project", pluck="name"):
        refresh_project_financials(project)
