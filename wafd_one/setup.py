from __future__ import annotations

from pathlib import Path

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

# Child tables first, then masters, then transactional documents.
DOCTYPE_FILES = (
    "wafd_meal_plan_item",
    "wafd_project_hotel",
    "wafd_project_service",
    "wafd_purchase_order_item",
    "wafd_recipe_item",
    "wafd_stock_movement_item",
    "wafd_mission",
    "wafd_hotel",
    "wafd_ingredient",
    "wafd_supplier",
    "wafd_vehicle",
    "wafd_driver",
    "wafd_warehouse",
    "wafd_recipe",
    "wafd_contract",
    "wafd_catering_project",
    "wafd_meal_plan",
    "wafd_production_batch",
    "wafd_quality_inspection",
    "wafd_loading_record",
    "wafd_delivery_trip",
    "wafd_delivery_proof",
    "wafd_complaint",
    "wafd_purchase_order",
    "wafd_stock_movement",
    "wafd_project_cost",
    "wafd_project_revenue",
    "wafd_invoice",
)

WORKSPACE_LINKS = (
    "WAFD Catering Project",
    "WAFD Mission",
    "WAFD Hotel",
    "WAFD Contract",
    "WAFD Meal Plan",
    "WAFD Recipe",
    "WAFD Ingredient",
)


def ensure_roles() -> None:
    for role_name in ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": 1,
                }
            ).insert(ignore_permissions=True)


def sync_doctypes() -> None:
    """Reload every WAFD ONE DocType from the repository into the site database."""
    for doctype_file in DOCTYPE_FILES:
        frappe.reload_doc(
            "wafd_one",
            "doctype",
            doctype_file,
            force=True,
            reset_permissions=True,
        )


def ensure_system_manager_access() -> None:
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


def reload_workspace() -> bool:
    missing = [name for name in WORKSPACE_LINKS if not frappe.db.exists("DocType", name)]
    if missing:
        frappe.throw(
            "WAFD ONE metadata sync incomplete. Missing DocTypes: " + ", ".join(missing)
        )

    frappe.reload_doc("wafd_one", "workspace", "wafd_one", force=True)
    return True


def ensure_default_app() -> None:
    settings = frappe.get_single("System Settings")
    if settings.meta.has_field("default_app") and settings.default_app != "wafd_one":
        settings.default_app = "wafd_one"
        settings.flags.ignore_permissions = True
        settings.flags.ignore_version = True
        settings.save()


def apply_setup(force_rebuild: bool = False, assign_manager_access: bool = True) -> None:
    """Backward-compatible setup entry point used by older installed patches."""
    ensure_roles()
    sync_doctypes()
    reload_workspace()
    if assign_manager_access:
        ensure_system_manager_access()
    ensure_default_app()
    frappe.clear_cache()


def before_migrate() -> None:
    # Permission rows in DocType JSON files reference these roles.
    ensure_roles()


def after_install() -> None:
    apply_setup(force_rebuild=True, assign_manager_access=True)


def after_migrate() -> None:
    # Also runs on sites where an older patch was already marked as executed.
    apply_setup(force_rebuild=True, assign_manager_access=True)
