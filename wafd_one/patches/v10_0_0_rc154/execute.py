"""RC154: quality-inspector dependency access and CCP one-sided-limit fix."""
import frappe


def execute():
    # Reload the project permission metadata so Quality Inspector can resolve
    # the project linked from Production Batch without broad edit rights.
    frappe.reload_doc("wafd_one", "doctype", "wafd_catering_project", force=True, reset_permissions=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_ccp_check", force=True, reset_permissions=True)
    frappe.clear_cache()
