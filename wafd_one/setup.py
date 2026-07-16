import frappe


ROLES = (
    "WAFD Operations Manager",
    "WAFD Project Manager",
    "WAFD Production Supervisor",
    "WAFD Quality Inspector",
    "WAFD Delivery Supervisor",
    "WAFD Driver",
    "WAFD Finance User",
    "WAFD Storekeeper",
)

WORKSPACE_REQUIRED_DOCTYPES = (
    "WAFD Catering Project",
    "WAFD Mission",
    "WAFD Hotel",
    "WAFD Contract",
    "WAFD Meal Plan",
    "WAFD Recipe",
    "WAFD Ingredient",
)


def ensure_roles():
    """Create roles referenced by DocType permission rows before model sync."""
    for role_name in ROLES:
        if not frappe.db.exists("Role", role_name):
            role = frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": 1,
                }
            )
            role.flags.ignore_permissions = True
            role.insert()


def reload_workspace():
    """Refresh the standard workspace only after every linked DocType exists."""
    missing = [
        doctype_name
        for doctype_name in WORKSPACE_REQUIRED_DOCTYPES
        if not frappe.db.exists("DocType", doctype_name)
    ]
    if missing:
        frappe.log_error(
            message="Missing DocTypes after model sync: " + ", ".join(missing),
            title="WAFD ONE workspace was not refreshed",
        )
        return False

    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=True)
    return True


def ensure_default_app():
    """Set WAFD ONE as default app when the installed Frappe version supports it."""
    try:
        settings = frappe.get_single("System Settings")
        if settings.meta.has_field("default_app") and settings.default_app != "wafd_one":
            settings.default_app = "wafd_one"
            settings.flags.ignore_permissions = True
            settings.flags.ignore_version = True
            settings.save()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WAFD ONE default app setup")


def before_migrate():
    ensure_roles()


def after_install():
    ensure_roles()
    reload_workspace()
    ensure_default_app()
    frappe.clear_cache()


def after_migrate():
    # At this point Frappe has completed standard model synchronization, so all
    # workspace links can be validated safely.
    ensure_roles()
    reload_workspace()
    ensure_default_app()
    frappe.clear_cache()
