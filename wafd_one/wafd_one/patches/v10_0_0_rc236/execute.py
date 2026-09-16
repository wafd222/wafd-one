"""RC236: synchronize unified WAFD employee account management."""

import frappe


def execute():
    from wafd_one.setup import ensure_roles

    ensure_roles()
    frappe.reload_doc("wafd_one", "page", "wafd_employee_team", force=True)
    frappe.clear_cache()
