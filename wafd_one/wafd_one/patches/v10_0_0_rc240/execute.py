"""RC240: expose loading-photo capture directly inside the loading form."""

import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_loading_record", force=True)
    frappe.clear_cache()
