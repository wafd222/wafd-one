import frappe


def execute():
    from wafd_one.setup import ensure_administration_page_and_workspace

    ensure_administration_page_and_workspace()
    frappe.clear_cache()
