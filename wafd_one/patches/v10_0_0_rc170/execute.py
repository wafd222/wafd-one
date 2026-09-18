import frappe


def execute():
    """Refresh website routing/cache after moving the client portal page to the app www root."""
    frappe.clear_cache()
    try:
        frappe.clear_website_cache()
    except Exception:
        # clear_cache is sufficient on builds where clear_website_cache is unavailable.
        pass
