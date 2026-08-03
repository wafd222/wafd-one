import frappe


def execute():
    for name in (
        "wafd_governance_settings",
        "wafd_approval_request",
        "wafd_audit_event",
    ):
        frappe.reload_doc("wafd_one", "doctype", name, force=True, reset_permissions=True)
    frappe.clear_cache()
