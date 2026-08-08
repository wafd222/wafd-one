import frappe


def execute():
    if not frappe.db.exists("DocType", "WAFD Packaging Record"):
        return
    for row in frappe.get_all("WAFD Packaging Record", fields=["name"]):
        try:
            doc = frappe.get_doc("WAFD Packaging Record", row.name)
            doc.flags.ignore_permissions = True
            doc.save()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "WAFD rc15 packaging repair")
    frappe.clear_cache()
