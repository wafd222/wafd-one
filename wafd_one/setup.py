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

# Child tables and independent masters first; linked parent documents last.
PHASE_ONE_DOCTYPE_FILES = (
    "wafd_project_hotel",
    "wafd_project_service",
    "wafd_recipe_item",
    "wafd_meal_plan_item",
    "wafd_mission",
    "wafd_hotel",
    "wafd_ingredient",
    "wafd_recipe",
    "wafd_contract",
    "wafd_catering_project",
    "wafd_meal_plan",
)


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


def ensure_system_manager_access():
    users = frappe.get_all(
        "Has Role",
        filters={"role": "System Manager", "parenttype": "User"},
        pluck="parent",
    )
    for user_name in users:
        if user_name == "Guest" or not frappe.db.get_value("User", user_name, "enabled"):
            continue
        user = frappe.get_doc("User", user_name)
        if "WAFD Operations Manager" not in {row.role for row in user.roles}:
            user.append("roles", {"role": "WAFD Operations Manager"})
            user.flags.ignore_permissions = True
            user.flags.ignore_version = True
            user.save()


def reload_workspace():
    """Load the standard Workspace through Frappe's metadata loader.

    This is safer than manually inserting a Workspace document and guarantees
    that child rows and link validation follow the framework's normal sync path.
    """
    required = (
        "WAFD Catering Project",
        "WAFD Mission",
        "WAFD Hotel",
        "WAFD Contract",
        "WAFD Meal Plan",
        "WAFD Recipe",
        "WAFD Ingredient",
    )
    missing = [name for name in required if not frappe.db.exists("DocType", name)]
    if missing:
        frappe.log_error(
            title="WAFD ONE workspace deferred",
            message=f"Missing DocTypes: {', '.join(missing)}",
        )
        return False

    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=True)
    return True


def ensure_default_app():
    try:
        settings = frappe.get_single("System Settings")
        if settings.meta.has_field("default_app"):
            settings.default_app = "wafd_one"
            settings.flags.ignore_permissions = True
            settings.flags.ignore_version = True
            settings.save()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WAFD ONE default app setup")


def before_migrate():
    # Roles referenced by DocType permissions must exist before model sync.
    ensure_roles()


def after_install():
    ensure_roles()
    reload_workspace()
    ensure_system_manager_access()
    ensure_default_app()
    frappe.clear_cache()


def after_migrate():
    ensure_roles()
    reload_workspace()
    ensure_system_manager_access()
    ensure_default_app()
    frappe.clear_cache()
