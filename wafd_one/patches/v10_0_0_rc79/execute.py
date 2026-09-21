import frappe


def execute():
    """Recalculate project financials after inventory consumption costing fix."""
    if not frappe.db.exists("DocType", "WAFD Catering Project"):
        return
    from wafd_one.finance import refresh_project_financials
    for project_name in frappe.get_all("WAFD Catering Project", pluck="name"):
        try:
            refresh_project_financials(project_name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"RC79 financial refresh: {project_name}")
