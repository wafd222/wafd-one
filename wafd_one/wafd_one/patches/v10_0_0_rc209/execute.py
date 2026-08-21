"""RC209: multi-user undertaking team management."""
import frappe


def execute():
    # Page metadata is shipped with the app; ensure operational roles exist and clear caches.
    from wafd_one.setup import ensure_roles
    ensure_roles()
    frappe.clear_cache()
