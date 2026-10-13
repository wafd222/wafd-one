import frappe


def execute():
    """Install bilingual quotation fields and refresh routing/print metadata."""
    from wafd_one.setup import ensure_quotation_print_format

    frappe.reload_doc("wafd_one", "doctype", "wafd_quotation", force=True)
    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    ensure_quotation_print_format()
    frappe.clear_cache(doctype="WAFD Quotation")
    frappe.clear_cache()
