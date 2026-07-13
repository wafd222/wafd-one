import frappe

ROLES = [
    "WAFD Operations Manager",
    "WAFD Project Manager",
    "WAFD Production Supervisor",
    "WAFD Quality Inspector",
    "WAFD Delivery Supervisor",
    "WAFD Driver",
    "WAFD Finance User",
    "WAFD Storekeeper",
]


def ensure_roles():
    for role_name in ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": 1,
                }
            ).insert(ignore_permissions=True)


def ensure_workspace_visibility():
    """Keep the standard workspace public and visible after every migration."""
    if frappe.db.exists("Workspace", "WAFD ONE"):
        frappe.db.set_value(
            "Workspace",
            "WAFD ONE",
            {"public": 1, "is_hidden": 0},
            update_modified=False,
        )


def after_install():
    ensure_roles()
    ensure_workspace_visibility()
    frappe.clear_cache()


def after_migrate():
    ensure_roles()
    ensure_workspace_visibility()
    frappe.clear_cache()
