import frappe


def execute():
    for doctype in (
        "WAFD Production Batch",
        "WAFD Loading Record",
        "WAFD Delivery Trip",
    ):
        frappe.reload_doc("wafd_one", "doctype", frappe.scrub(doctype), force=True)
