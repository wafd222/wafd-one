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

# Ordered to load child tables and independent masters before linked parents.
ALL_DOCTYPE_FILES = (
    "wafd_meal_plan_item",
    "wafd_project_hotel",
    "wafd_project_service",
    "wafd_purchase_order_item",
    "wafd_recipe_item",
    "wafd_stock_movement_item",
    "wafd_driver",
    "wafd_hotel",
    "wafd_mission",
    "wafd_supplier",
    "wafd_vehicle",
    "wafd_warehouse",
    "wafd_ingredient",
    "wafd_recipe",
    "wafd_catering_project",
    "wafd_contract",
    "wafd_meal_plan",
    "wafd_loading_record",
    "wafd_production_batch",
    "wafd_delivery_trip",
    "wafd_delivery_proof",
    "wafd_quality_inspection",
    "wafd_complaint",
    "wafd_invoice",
    "wafd_project_cost",
    "wafd_project_revenue",
    "wafd_purchase_order",
    "wafd_stock_movement",
)

REQUIRED_WORKSPACE_DOCTYPES = (
    "WAFD Catering Project",
    "WAFD Mission",
    "WAFD Hotel",
    "WAFD Contract",
    "WAFD Meal Plan",
    "WAFD Recipe",
    "WAFD Ingredient",
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


def sync_all_doctypes():
    """Reload every WAFD ONE DocType JSON into the current site database."""
    for doctype_file in ALL_DOCTYPE_FILES:
        frappe.reload_doc(
            "wafd_one",
            "doctype",
            doctype_file,
            force=True,
            reset_permissions=True,
        )

    # Reload the two mutually linked documents after both records exist.
    frappe.reload_doc(
        "wafd_one", "doctype", "wafd_catering_project", force=True, reset_permissions=True
    )
    frappe.reload_doc(
        "wafd_one", "doctype", "wafd_contract", force=True, reset_permissions=True
    )


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


def reload_workspace(force_rebuild=False):
    missing = [
        name for name in REQUIRED_WORKSPACE_DOCTYPES
        if not frappe.db.exists("DocType", name)
    ]
    if missing:
        frappe.throw(
            "WAFD ONE metadata synchronization is incomplete. Missing DocTypes: "
            + ", ".join(missing)
        )

    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=bool(force_rebuild))
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


def apply_setup(force_rebuild=False, assign_manager_access=True, sync_doctypes=False):
    """Compatibility entry point used by historical and current patches."""
    ensure_roles()
    if sync_doctypes:
        sync_all_doctypes()
    reload_workspace(force_rebuild=force_rebuild)
    if assign_manager_access:
        ensure_system_manager_access()
    ensure_default_app()


def before_migrate():
    ensure_roles()


def after_install():
    apply_setup(force_rebuild=True, assign_manager_access=True, sync_doctypes=True)
    frappe.clear_cache()


def after_migrate():
    # Normal migrations sync metadata automatically. The v2.6 patch repairs
    # older sites once; this hook then keeps workspace/access settings current.
    apply_setup(force_rebuild=True, assign_manager_access=True, sync_doctypes=False)
    frappe.clear_cache()
