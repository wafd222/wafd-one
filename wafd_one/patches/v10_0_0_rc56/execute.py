import frappe


def execute():
    """Migrate legacy WAFD Payment status records to Frappe docstatus."""
    if not frappe.db.exists("DocType", "WAFD Payment"):
        return

    frappe.db.sql(
        """update `tabWAFD Payment`
           set docstatus=1
           where status='معتمد / Confirmed' and docstatus=0"""
    )
    frappe.db.sql(
        """update `tabWAFD Payment`
           set docstatus=2
           where status='ملغي / Cancelled' and docstatus!=2"""
    )
    frappe.clear_cache(doctype="WAFD Payment")

    # Recalculate every affected invoice from submitted payments only.
    from wafd_one.finance import refresh_invoice_and_project
    for invoice in frappe.get_all("WAFD Invoice", pluck="name"):
        refresh_invoice_and_project(invoice)
