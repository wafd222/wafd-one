import frappe


def get_context(context):
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and not ({"System Manager", "WAFD Operations Manager"} & roles):
        frappe.throw("Not permitted", frappe.PermissionError)
    return context
