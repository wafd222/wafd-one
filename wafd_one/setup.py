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
    "wafd_invoice_item",
    "wafd_production_material",
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
    "wafd_packaging_record",
    "wafd_loading_record",
    "wafd_production_batch",
    "wafd_delivery_trip",
    "wafd_delivery_proof",
    "wafd_quality_inspection",
    "wafd_complaint",
    "wafd_invoice",
    "wafd_project_cost",
    "wafd_project_revenue",
    "wafd_payment",
    "wafd_purchase_order",
    "wafd_stock_balance",
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


def _workspace_source_path():
    from pathlib import Path

    return (
        Path(__file__).resolve().parent
        / "wafd_one"
        / "workspace"
        / "wafd_one"
        / "wafd_one.json"
    )


def _load_workspace_source():
    import json

    with _workspace_source_path().open(encoding="utf-8") as source:
        workspace = json.load(source)

    # Explicit v16 ownership fields. ``app`` is important for the persistent
    # sidebar/app routing introduced in Frappe v16.
    workspace.update(
        {
            "doctype": "Workspace",
            "name": "WAFD ONE",
            "label": "WAFD ONE",
            "title": "WAFD ONE",
            "module": "WAFD ONE",
            "app": "wafd_one",
            "type": "Workspace",
            "public": 1,
            "for_user": "",
            "is_hidden": 0,
        }
    )
    return workspace


def _validate_workspace_record(workspace):
    expected = {
        "المشاريع": "WAFD Catering Project",
        "البعثات والعملاء": "WAFD Mission",
        "الفنادق": "WAFD Hotel",
        "العقود": "WAFD Contract",
        "خطط الوجبات": "WAFD Meal Plan",
        "الوصفات": "WAFD Recipe",
        "مكونات الأغذية": "WAFD Ingredient",
    }
    actual = {row.label: row.link_to for row in workspace.shortcuts}
    missing = [label for label, target in expected.items() if actual.get(label) != target]
    if missing:
        frappe.throw(
            "WAFD ONE workspace rebuild failed. Missing shortcuts: "
            + ", ".join(missing)
        )

    import json

    blocks = json.loads(workspace.content or "[]")
    block_names = {
        row.get("data", {}).get("shortcut_name")
        for row in blocks
        if row.get("type") == "shortcut"
    }
    missing_blocks = [label for label in expected if label not in block_names]
    if missing_blocks:
        frappe.throw(
            "WAFD ONE workspace content is incomplete. Missing blocks: "
            + ", ".join(missing_blocks)
        )


def rebuild_workspace_from_source():
    missing = [
        name for name in REQUIRED_WORKSPACE_DOCTYPES
        if not frappe.db.exists("DocType", name)
    ]
    if missing:
        frappe.throw(
            "WAFD ONE metadata synchronization is incomplete. Missing DocTypes: "
            + ", ".join(missing)
        )

    workspace_data = _load_workspace_source()

    # A savepoint prevents leaving the site without a workspace if validation
    # fails after deleting an older/incomplete record.
    savepoint = "wafd_one_workspace_rebuild"
    frappe.db.savepoint(savepoint)
    try:
        if frappe.db.exists("Workspace", "WAFD ONE"):
            frappe.delete_doc(
                "Workspace",
                "WAFD ONE",
                force=True,
                ignore_permissions=True,
            )

        workspace = frappe.get_doc(workspace_data)
        workspace.flags.ignore_permissions = True
        workspace.flags.ignore_version = True
        workspace.insert(ignore_permissions=True)
        workspace.reload()
        _validate_workspace_record(workspace)
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise

    # Workspace and permission data are cached per user for several hours.
    frappe.clear_cache()
    return True


def reload_workspace(force_rebuild=False):
    # Kept as the historical public entry point. A forced rebuild now performs
    # a deterministic database reconstruction instead of relying on reload_doc.
    if force_rebuild or not frappe.db.exists("Workspace", "WAFD ONE"):
        return rebuild_workspace_from_source()

    workspace = frappe.get_doc("Workspace", "WAFD ONE")
    try:
        _validate_workspace_record(workspace)
    except Exception:
        return rebuild_workspace_from_source()
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
    ensure_administration_page_and_workspace()
    frappe.clear_cache()


def after_migrate():
    # Frappe v16 can incorrectly remove valid custom-app DocTypes during
    # remove_orphan_doctypes. Reload WAFD ONE metadata before rebuilding
    # the workspace so the migration can recover safely.
    apply_setup(
        force_rebuild=True,
        assign_manager_access=True,
        sync_doctypes=True,
    )
    ensure_administration_page_and_workspace()
    frappe.clear_cache()


def ensure_administration_page_and_workspace():
    """Synchronize the administration Page and expose it as a visible workspace.

    This is deliberately executed after every migrate because some Frappe Cloud
    upgrades can remove standard Page/Workspace records from custom apps.
    """
    import json
    from pathlib import Path

    # Reload the standard page metadata first so Page links never point to a
    # missing record.
    frappe.reload_doc(
        "wafd_one", "page", "wafd_administration", force=True, reset_permissions=True
    )

    page_name = "wafd-administration"
    if not frappe.db.exists("Page", page_name):
        frappe.throw("WAFD Administration page synchronization failed.")

    source_path = (
        Path(__file__).resolve().parent
        / "wafd_one"
        / "workspace"
        / "wafd_administration"
        / "wafd_administration.json"
    )
    with source_path.open(encoding="utf-8") as source:
        data = json.load(source)

    workspace_name = "إدارة WAFD ONE"
    data.update({
        "doctype": "Workspace",
        "name": workspace_name,
        "label": workspace_name,
        "title": workspace_name,
        "module": "WAFD ONE",
        "app": "wafd_one",
        "public": 1,
        "for_user": "",
        "is_hidden": 0,
        # Keep it top-level. A child workspace may not be shown in the app
        # sidebar until its parent has already been opened.
        "parent_page": "",
    })

    if frappe.db.exists("Workspace", workspace_name):
        frappe.delete_doc(
            "Workspace", workspace_name, force=True, ignore_permissions=True
        )

    workspace = frappe.get_doc(data)
    workspace.flags.ignore_permissions = True
    workspace.flags.ignore_version = True
    workspace.insert(ignore_permissions=True)
    workspace.reload()

    shortcuts = {row.label: row.link_to for row in workspace.shortcuts}
    if shortcuts.get("فتح إدارة WAFD ONE") != page_name:
        frappe.throw("WAFD Administration workspace shortcut synchronization failed.")
    if workspace.is_hidden or not workspace.public or workspace.parent_page:
        frappe.throw("WAFD Administration workspace visibility validation failed.")
    if workspace.app != "wafd_one":
        frappe.throw("WAFD Administration workspace app ownership validation failed.")

    frappe.clear_cache()
    return True
