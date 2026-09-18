"""RC197: grant undertaking officers read/select access to required reference lists only."""
import frappe


def execute():
    for dt, module, name in (
        ("WAFD Hotel", "wafd_one", "wafd_hotel"),
        ("WAFD Nationality", "wafd_one", "wafd_nationality"),
        ("WAFD Undertaking Beneficiary", "wafd_one", "wafd_undertaking_beneficiary"),
    ):
        if frappe.db.exists("DocType", dt):
            frappe.reload_doc(module, "doctype", name, force=True, reset_permissions=True)
            frappe.clear_cache(doctype=dt)
    frappe.clear_cache()
