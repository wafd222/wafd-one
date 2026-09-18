import frappe


def execute():
    """Re-verify the administration Page and Workspace after upgrading assets."""
    from wafd_one.setup import ensure_administration_page_and_workspace

    ensure_administration_page_and_workspace()
    frappe.clear_cache()
