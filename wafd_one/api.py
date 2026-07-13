import frappe


def check_app_permission():
    """Allow desk users to see WAFD ONE in the Frappe apps page."""
    if frappe.session.user == "Guest":
        return False
    return bool(frappe.get_cached_value("User", frappe.session.user, "user_type") == "System User")
