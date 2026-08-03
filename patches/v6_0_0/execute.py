import frappe

def execute():
    for name in ("wafd_governance_settings", "wafd_approval_request", "wafd_audit_event"):
        frappe.reload_doc("wafd_one", "doctype", name, force=True, reset_permissions=True)
    from wafd_one.setup import ensure_roles
    ensure_roles()
    settings=frappe.get_single("WAFD Governance Settings")
    if not settings.approver_role:
        settings.approver_role="WAFD Approver"
    if not settings.audit_retention_days:
        settings.audit_retention_days=2555
    settings.flags.ignore_permissions=True
    settings.save(ignore_permissions=True)
    frappe.clear_cache()
