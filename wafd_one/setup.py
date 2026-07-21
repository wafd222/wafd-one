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
    "WAFD Approver",
    "WAFD Auditor",
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
    "wafd_food_safety_settings",
    "wafd_governance_settings",
    "wafd_approval_request",
    "wafd_audit_event",
    "wafd_ccp_check",
    "wafd_data_source",
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

# Backward-compatible Phase 1 subset used by historical repair patches.
PHASE_ONE_DOCTYPE_FILES = (
    "wafd_mission",
    "wafd_hotel",
    "wafd_supplier",
    "wafd_ingredient",
    "wafd_recipe_item",
    "wafd_recipe",
    "wafd_meal_plan_item",
    "wafd_project_hotel",
    "wafd_project_service",
    "wafd_catering_project",
    "wafd_contract",
    "wafd_meal_plan",
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
        "إدارة WAFD ONE": "wafd-administration-console",
    }
    actual = {row.label: row.link_to for row in workspace.shortcuts}
    missing = [label for label, target in expected.items() if actual.get(label) != target]
    if missing:
        frappe.throw(
            "WAFD ONE workspace rebuild failed. Missing shortcuts: "
            + ", ".join(missing)
        )

    admin_shortcut = next(
        (row for row in workspace.shortcuts if row.label == "إدارة WAFD ONE"),
        None,
    )
    if not admin_shortcut or admin_shortcut.type != "Page":
        frappe.throw("WAFD ONE administration shortcut must target a Desk Page.")

    admin_link = next(
        (row for row in workspace.links if row.label == "إدارة WAFD ONE"),
        None,
    )
    if (
        not admin_link
        or admin_link.link_type != "Page"
        or admin_link.link_to != "wafd-administration-console"
    ):
        frappe.throw("WAFD ONE administration workspace link is invalid.")

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


def ensure_administration_page_and_workspace():
    """Backward-compatible entry point for historical administration patches."""
    ensure_administration_page()

    for obsolete_workspace in ("WAFD Administration", "إدارة WAFD ONE"):
        if obsolete_workspace != "WAFD ONE" and frappe.db.exists("Workspace", obsolete_workspace):
            frappe.delete_doc(
                "Workspace",
                obsolete_workspace,
                force=True,
                ignore_permissions=True,
            )

    return rebuild_workspace_from_source()


def ensure_administration_page():
    """Synchronize and validate the canonical Desk Page route."""
    page_name = "wafd-administration-console"
    frappe.reload_doc(
        "wafd_one",
        "page",
        "wafd_administration_console",
        force=True,
    )
    if not frappe.db.exists("Page", page_name):
        frappe.throw("WAFD Administration Console Page was not created during synchronization.")
    page = frappe.get_doc("Page", page_name)
    if page.module != "WAFD ONE" or page.page_name != page_name:
        frappe.throw("WAFD Administration Console Page metadata validation failed.")
    required_roles = {"System Manager", "WAFD Operations Manager"}
    actual_roles = {row.role for row in page.roles}
    if not required_roles.issubset(actual_roles):
        frappe.throw("WAFD Administration Console Page permissions are incomplete.")
    frappe.clear_cache()
    return True


def ensure_administration_console():
    """Synchronize and validate the canonical administration Single DocType.

    ``frappe.reload_doc`` is the supported first path.  If a site has stale
    module metadata or the record was removed as an orphan, the fallback uses
    Frappe's own JSON importer rather than inserting a standard DocType
    directly.  This preserves the framework's schema, permission and module
    synchronization behavior.
    """
    from pathlib import Path

    from frappe.modules.import_file import import_file_by_path

    doctype_name = "WAFD Administration Console"
    source_path = (
        Path(__file__).resolve().parent
        / "wafd_one"
        / "doctype"
        / "wafd_administration_console"
        / "wafd_administration_console.json"
    )
    if not source_path.is_file():
        frappe.throw(f"Missing administration console metadata file: {source_path}")

    frappe.reload_doc(
        "wafd_one",
        "doctype",
        "wafd_administration_console",
        force=True,
        reset_permissions=True,
    )

    if not frappe.db.exists("DocType", doctype_name):
        import_file_by_path(
            str(source_path),
            force=True,
            ignore_version=True,
            reset_permissions=True,
        )

    if not frappe.db.exists("DocType", doctype_name):
        frappe.throw(
            "WAFD Administration Console was not created after metadata synchronization."
        )

    meta = frappe.get_doc("DocType", doctype_name)
    failures = []
    if not meta.issingle:
        failures.append("issingle must be enabled")
    if meta.custom:
        failures.append("custom must be disabled")
    if meta.module != "WAFD ONE":
        failures.append("module must be WAFD ONE")
    if getattr(meta, "hide_from_search", 0):
        failures.append("hide_from_search must be disabled")

    required_roles = {"System Manager", "WAFD Operations Manager"}
    actual_roles = {row.role for row in meta.permissions}
    missing_roles = sorted(required_roles - actual_roles)
    if missing_roles:
        failures.append("missing permissions for " + ", ".join(missing_roles))

    if failures:
        frappe.throw(
            "WAFD Administration Console metadata validation failed: "
            + "; ".join(failures)
        )

    # Confirm that the controller can be imported.  This is the same class of
    # validation used by Frappe when detecting orphan standard DocTypes.
    frappe.get_meta(doctype_name)
    frappe.clear_cache(doctype=doctype_name)
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
    ensure_administration_page()
    reload_workspace(force_rebuild=force_rebuild)
    if assign_manager_access:
        ensure_system_manager_access()
    ensure_default_app()


def before_migrate():
    ensure_roles()


def after_install():
    apply_setup(force_rebuild=True, assign_manager_access=True, sync_doctypes=True)
    frappe.clear_cache()



def ensure_hotel_undertaking_print_format():
    """Force the safe undertaking template into every legacy matching format.

    This deliberately runs after every migration because old sites may retain a
    database copy of the Jinja template even after the standard JSON was synced.
    """
    source = (
        Path(__file__).resolve().parent
        / "wafd_one"
        / "print_format"
        / "wafd_hotel_undertaking"
        / "wafd_hotel_undertaking.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    canonical_name = data["name"]
    safe_html = data.get("html") or ""

    if "get_single" in safe_html:
        raise RuntimeError("Unsafe get_single call found in undertaking template source")

    names = set(
        frappe.get_all(
            "Print Format",
            filters={"doc_type": "WAFD Hotel Undertaking"},
            pluck="name",
        )
    )
    names.add(canonical_name)

    for name in names:
        if frappe.db.exists("Print Format", name):
            doc = frappe.get_doc("Print Format", name)
            # Repair the canonical format and every legacy copy that contains
            # the removed unsafe call. This prevents the old URL/selection from
            # continuing to open a broken database template.
            if name != canonical_name and "get_single" not in (doc.html or ""):
                continue
            doc.html = safe_html
            doc.doc_type = "WAFD Hotel Undertaking"
            doc.custom_format = 1
            doc.print_format_type = "Jinja"
            doc.disabled = 0
            doc.raw_printing = 0
            doc.save(ignore_permissions=True)
        else:
            frappe.get_doc(data).insert(ignore_permissions=True)

    frappe.clear_cache(doctype="Print Format")

def after_migrate():
    ensure_hotel_undertaking_print_format()
    # The framework has already synchronized all application DocTypes before
    # this hook runs.  Re-sync only the administration console recovery path,
    # then rebuild navigation.  Avoid reloading every operational DocType a
    # second time on each migration.
    apply_setup(
        force_rebuild=True,
        assign_manager_access=True,
        sync_doctypes=False,
    )
    frappe.clear_cache()
