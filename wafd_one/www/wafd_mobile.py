import frappe


def get_context(context):
    """Role-aware PWA launch route used by the web manifest."""
    context.no_cache = 1
    user = frappe.session.user
    if user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/wafd-mobile"
        raise frappe.Redirect

    roles = set(frappe.get_roles(user))
    if "WAFD Client Portal User" in roles and not ({"System Manager", "WAFD Operations Manager"} & roles):
        target = "/wafd-client"
    else:
        target = "/desk/wafd-role-home"
    frappe.local.flags.redirect_location = target
    raise frappe.Redirect
