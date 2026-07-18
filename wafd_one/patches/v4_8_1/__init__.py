import frappe


def execute():
    """Force-sync and validate the standard administration console."""
    frappe.reload_doc(
        "wafd_one",
        "doctype",
        "wafd_administration_console",
        force=True,
        reset_permissions=True,
    )

    if not frappe.db.exists("DocType", "WAFD Administration Console"):
        frappe.throw("WAFD Administration Console DocType synchronization failed.")

    meta = frappe.get_meta("WAFD Administration Console")
    if not meta.issingle:
        frappe.throw("WAFD Administration Console must be a Single DocType.")

    from wafd_one.setup import rebuild_workspace_from_source

    rebuild_workspace_from_source()

    workspace = frappe.get_doc("Workspace", "WAFD ONE")
    shortcut = next(
        (
            row
            for row in workspace.shortcuts
            if row.label == "إدارة WAFD ONE"
        ),
        None,
    )
    if not shortcut or shortcut.link_to != "WAFD Administration Console":
        frappe.throw("WAFD Administration Console workspace shortcut validation failed.")

    frappe.clear_cache()
