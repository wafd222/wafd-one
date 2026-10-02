"""Install the isolated Iftar viewer role and refresh only affected pages."""

import frappe

from wafd_one.setup import ensure_roles


IFTAR_VIEWER_ROLE = "WAFD Iftar External Viewer"


def execute():
    ensure_roles()

    # Preserve all existing roles. Existing project followers receive the new
    # isolated Iftar role so upgrades do not hide their already assigned work.
    users = frappe.get_all(
        "WAFD Iftar Project",
        filters={"external_viewer_user": ["is", "set"]},
        pluck="external_viewer_user",
        limit_page_length=5000,
    )
    for user in sorted(set(users) - {"", "Guest"}):
        if not frappe.db.exists("User", {"name": user, "enabled": 1}):
            continue
        account = frappe.get_doc("User", user)
        if IFTAR_VIEWER_ROLE not in {row.role for row in account.roles}:
            account.add_roles(IFTAR_VIEWER_ROLE)

    for page in ("wafd_role_home", "wafd_delivery_viewer", "wafd_iftar_team"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()
