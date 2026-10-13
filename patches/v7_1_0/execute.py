import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_finance_settings", force=True, reset_permissions=True)
    from wafd_one.finance import refresh_overdue_invoices
    refresh_overdue_invoices()
