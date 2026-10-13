import frappe


def execute():
    """Install the standalone quotation metadata in dependency order."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation_item", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    frappe.clear_cache(doctype="WAFD Quotation")
