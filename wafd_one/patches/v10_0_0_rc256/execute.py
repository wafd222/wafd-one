import frappe


def execute():
    """Install reliable image attachment metadata and the 3-page print format."""
    from wafd_one.setup import ensure_quotation_file_permissions, ensure_quotation_print_format

    frappe.reload_doc(
        "wafd_one", "doctype", "wafd_quotation", force=True, reset_permissions=True
    )
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    ensure_quotation_print_format()
    ensure_quotation_file_permissions()
    frappe.clear_cache(doctype="File")
    frappe.clear_cache(doctype="WAFD Quotation")
    frappe.clear_cache()
