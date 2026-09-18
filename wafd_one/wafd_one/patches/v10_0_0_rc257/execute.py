import frappe


def execute():
    """Refresh the quotation print format with its corrected item heading."""
    from wafd_one.setup import ensure_quotation_print_format

    frappe.reload_doc("wafd_one", "print_format", "wafd_quotation", force=True)
    ensure_quotation_print_format()
    frappe.clear_cache(doctype="WAFD Quotation")
    frappe.clear_cache()
