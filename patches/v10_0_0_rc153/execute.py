"""RC153: repair Desk access for every WAFD operational role."""
import frappe


def execute():
    from wafd_one.setup import ensure_roles

    ensure_roles()
    # Role desk-access is cached in permission/session metadata.
    frappe.clear_cache()
