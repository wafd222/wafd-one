import frappe
from frappe.utils import cint

OFFICER = "WAFD Undertaking Officer"
PRIVILEGED = {"System Manager", "WAFD Operations Manager", "WAFD Undertaking Reviewer"}

def _roles(user):
    return set(frappe.get_roles(user))

def _officer_is_enabled(user):
    if not user or user == "Guest":
        return False
    return cint(frappe.db.get_value("User", user, "enabled") or 0) == 1

def undertaking_query(user=None):
    user = user or frappe.session.user
    roles = _roles(user)
    if OFFICER in roles and not (roles & PRIVILEGED):
        # RC214: an officer disabled by management must lose undertaking access
        # immediately, including from a browser session that was already open.
        if not _officer_is_enabled(user):
            return "1=0"
        return f"`tabWAFD Hotel Undertaking`.`owner` = {frappe.db.escape(user)}"
    return ""

def undertaking_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    roles = _roles(user)
    # Frappe v16 requires has_permission hooks to explicitly return True when
    # the hook does not deny access. Returning None can deny access even when
    # the DocType role permissions allow it. Managers/reviewers must be able
    # to read every undertaking; row ownership applies only to pure officers.
    if user == "Administrator" or (roles & PRIVILEGED):
        return True
    if OFFICER not in roles:
        return True
    if not _officer_is_enabled(user):
        return False
    if permission_type == "create" or getattr(doc, "__islocal", False):
        return True
    return getattr(doc, "owner", None) == user
