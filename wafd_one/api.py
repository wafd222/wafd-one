import frappe


FIELD_ROLES = {"WAFD Driver", "WAFD Cleaning Supervisor", "WAFD Delivery Viewer"}


def boot_session(bootinfo):
    """Send field-only employees straight to the isolated WAFD role home."""
    user = frappe.session.user
    if not user or user == "Guest":
        return
    roles = set(frappe.get_roles(user))
    has_field_role = bool(roles & FIELD_ROLES)
    has_other_wafd_role = any(role.startswith("WAFD ") and role not in FIELD_ROLES for role in roles)
    if has_field_role and "System Manager" not in roles and not has_other_wafd_role:
        bootinfo.home_page = "wafd-role-home"
        bootinfo.wafd_force_role_home = 1


def check_app_permission():
    """Allow desk users to see WAFD ONE in the Frappe apps page."""
    if frappe.session.user == "Guest":
        return False
    return bool(frappe.get_cached_value("User", frappe.session.user, "user_type") == "System User")
