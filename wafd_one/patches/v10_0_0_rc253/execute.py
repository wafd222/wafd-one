import frappe


def execute():
    """Install quotation PDF pagination, assets and direct-action corrections."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation_item", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    from wafd_one.setup import ensure_quotation_print_format
    ensure_quotation_print_format()
    frappe.clear_cache(doctype="WAFD Quotation")
    frappe.clear_cache()
