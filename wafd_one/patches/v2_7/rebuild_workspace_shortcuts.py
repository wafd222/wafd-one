import frappe
from wafd_one.setup import ensure_roles, ensure_system_manager_access, sync_all_doctypes


def execute():
    """Rebuild WAFD ONE workspace so shortcut rows are recreated on existing sites."""
    ensure_roles()
    sync_all_doctypes()

    # Remove the old database copy. A normal reload can preserve stale child rows
    # on sites upgraded through several historical releases.
    if frappe.db.exists("Workspace", "WAFD ONE"):
        frappe.delete_doc(
            "Workspace",
            "WAFD ONE",
            force=True,
            ignore_permissions=True,
        )

    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=True)
    ensure_system_manager_access()
    frappe.clear_cache()
    frappe.db.commit()
