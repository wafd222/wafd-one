import frappe


def execute():
    """Install the standard Single DocType administration console and refresh navigation."""
    frappe.reload_doc(
        "wafd_one",
        "doctype",
        "wafd_administration_console",
        force=True,
        reset_permissions=True,
    )
    from wafd_one.setup import reload_workspace

    reload_workspace(force_rebuild=True)
    frappe.clear_cache()
