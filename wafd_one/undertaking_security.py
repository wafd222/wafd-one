import frappe

OFFICER = "WAFD Undertaking Officer"
PRIVILEGED = {"System Manager", "WAFD Operations Manager", "WAFD Undertaking Reviewer"}

def _roles(user):
    return set(frappe.get_roles(user))

def undertaking_query(user=None):
    user = user or frappe.session.user
    roles = _roles(user)
    if OFFICER in roles and not (roles & PRIVILEGED):
        return f"`tabWAFD Hotel Undertaking`.`owner` = {frappe.db.escape(user)}"
    return ""

def undertaking_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    roles = _roles(user)
    if OFFICER not in roles or (roles & PRIVILEGED):
        return None
    if permission_type == "create" or getattr(doc, "__islocal", False):
        return True
    return getattr(doc, "owner", None) == user
