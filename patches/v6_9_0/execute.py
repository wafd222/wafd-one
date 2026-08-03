import frappe


def execute():
    for name in ("wafd_invoice", "wafd_invoice_item", "wafd_payment", "wafd_catering_project"):
        frappe.reload_doc("wafd_one", "doctype", name, force=True, reset_permissions=True)

    invoices = frappe.get_all("WAFD Invoice", pluck="name")
    for invoice_name in invoices:
        frappe.enqueue(
            "wafd_one.finance.refresh_invoice_and_project",
            invoice_name=invoice_name,
            enqueue_after_commit=True,
        )
