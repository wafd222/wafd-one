import frappe


def get_context(context):
    context.no_cache = 1
    context.no_breadcrumbs = True
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/wafd-client"
        raise frappe.Redirect
    roles = set(frappe.get_roles(frappe.session.user))
    if "WAFD Client Portal User" not in roles and "System Manager" not in roles and "WAFD Operations Manager" not in roles:
        frappe.throw("غير مصرح لك باستخدام بوابة WAFD / WAFD client portal access denied", frappe.PermissionError)
    context.title = "WAFD Client Portal"
    return context
