import frappe


def execute():
    if not frappe.db.exists("DocType", "WAFD Catering Project"):
        return
    from wafd_one.finance import refresh_project_financials
    for name in frappe.get_all("WAFD Catering Project", pluck="name"):
        refresh_project_financials(name)
