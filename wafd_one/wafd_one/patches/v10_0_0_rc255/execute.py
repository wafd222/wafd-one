import frappe


def execute():
    """Install quotation ownership, lookup, upload and multi-task access."""
    from wafd_one.setup import (
        ensure_quotation_file_permissions,
        ensure_quotation_print_format,
        ensure_roles,
    )

    ensure_roles()
    for doctype_file in ("wafd_quotation", "wafd_mission", "wafd_hotel", "wafd_recipe"):
        frappe.reload_doc(
            "wafd_one", "doctype", doctype_file, force=True, reset_permissions=True
        )
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_employee_team", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    ensure_quotation_print_format()
    ensure_quotation_file_permissions()
    frappe.clear_cache()
