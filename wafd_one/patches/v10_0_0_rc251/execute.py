import frappe


def execute():
    """Re-sync quotation metadata after the RC250 child controller repair."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation_item", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    frappe.clear_cache(doctype="WAFD Quotation")
