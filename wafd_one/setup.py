import json
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
    "WAFD Approver",
    "WAFD Auditor",
)

# Ordered to load child tables and independent masters before linked parents.
ALL_DOCTYPE_FILES = tuple(
    sorted(
        path.name
        for path in (Path(__file__).resolve().parent / "wafd_one" / "doctype").iterdir()
        if path.is_dir() and not path.name.startswith("__")
        and (path / f"{path.name}.json").exists()
    )
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
    "WAFD Daily Meal Plan",
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
        "الخطط اليومية": "WAFD Daily Meal Plan",
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
    frappe.reload_doc("wafd_one", "page", "wafd_launch_center", force=True)
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
    ensure_hotel_undertaking_print_format()
    ensure_madinah_hotels_400()
    frappe.clear_cache()



def ensure_hotel_undertaking_print_format():
    """Force one safe template into every undertaking print format."""
    source = (
        Path(__file__).resolve().parent
        / "wafd_one" / "print_format" / "wafd_hotel_undertaking"
        / "wafd_hotel_undertaking.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    canonical_name = data["name"]
    safe_html = data.get("html") or ""
    forbidden = ("get_single", "frappe.get_doc", "frappe.db.sql")
    if any(token in safe_html for token in forbidden):
        raise RuntimeError("Unsafe server call found in undertaking template source")

    # Only touch formats that belong to this DocType. Never reassign unrelated
    # formats merely because their HTML contains a similar token.
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
            frappe.db.set_value("Print Format", name, {
                "html": safe_html,
                "doc_type": "WAFD Hotel Undertaking",
                "custom_format": 1,
                "print_format_type": "Jinja",
                "disabled": 0,
                "raw_printing": 0,
            }, update_modified=False)
        else:
            frappe.get_doc(data).insert(ignore_permissions=True)

    if frappe.db.has_column("DocType", "default_print_format"):
        frappe.db.set_value("DocType", "WAFD Hotel Undertaking", "default_print_format", canonical_name, update_modified=False)

    unsafe_formats = frappe.get_all(
        "Print Format",
        filters={"doc_type": "WAFD Hotel Undertaking"},
        fields=["name", "html"],
    )
    remaining = [
        row.name
        for row in unsafe_formats
        if any(token in (row.html or "") for token in forbidden)
    ]
    if remaining:
        raise RuntimeError(
            "Hotel Undertaking repair incomplete; unsafe format(s): "
            + ", ".join(remaining)
        )
    frappe.clear_cache(doctype="Print Format")


def ensure_madinah_hotels_400():
    """Add all missing records from the reviewed 400-row file without deletion."""
    import csv
    from frappe.utils import nowdate
    path = Path(__file__).resolve().parent / "reference_data" / "madinah_hotels_400_ota_review.csv"
    if not path.exists():
        raise RuntimeError(f"Hotel catalogue is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    expected_names = []
    seen = set()
    for row in rows:
        hotel_name = (row.get("hotel_name") or "").strip()
        if not hotel_name or hotel_name in seen:
            continue
        seen.add(hotel_name)
        expected_names.append(hotel_name)
        existing = frappe.db.get_value("WAFD Hotel", {"hotel_name": hotel_name}, "name")
        if existing:
            doc = frappe.get_doc("WAFD Hotel", existing)
            changed = False
            for fieldname in ("city", "district", "address", "source_authority", "source_url"):
                value = (row.get(fieldname) or "").strip()
                if value and not doc.get(fieldname):
                    doc.set(fieldname, value)
                    changed = True
            if not doc.get("verification_status"):
                doc.verification_status = "يحتاج مراجعة / Needs Review"
                changed = True
            if changed:
                doc.save(ignore_permissions=True)
            continue

        doc = frappe.new_doc("WAFD Hotel")
        doc.hotel_name = hotel_name
        doc.status = "نشط / Active"
        doc.city = (row.get("city") or "المدينة المنورة").strip()
        doc.district = (row.get("district") or "").strip()
        doc.address = (row.get("address") or "").strip()
        doc.verification_status = "يحتاج مراجعة / Needs Review"
        doc.source_authority = (row.get("source_authority") or "").strip()
        doc.source_url = (row.get("source_url") or "").strip()
        doc.source_notes = (row.get("verification_status") or "").strip()
        doc.last_verified_on = nowdate()
        doc.insert(ignore_permissions=True)

    if len(expected_names) != 400:
        raise RuntimeError(f"Hotel catalogue must contain 400 unique names; found {len(expected_names)}")
    installed = set(frappe.get_all("WAFD Hotel", filters={"hotel_name": ["in", expected_names]}, pluck="hotel_name"))
    missing = [name for name in expected_names if name not in installed]
    if missing:
        raise RuntimeError(f"Hotel catalogue installation incomplete: {len(missing)} record(s) missing")
    return {"catalogue_count": 400, "installed_count": len(installed)}


def ensure_madinah_central_and_nearby_hotels():
    """Install/update official central-map hotels and verified properties within 2 km; never delete user data."""
    import csv
    from frappe.utils import nowdate
    path = Path(__file__).resolve().parent / "reference_data" / "madinah_central_and_nearby_hotels_2026.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    installed = 0
    for row in rows:
        hotel_name = (row.get("hotel_name") or "").strip()
        if not hotel_name:
            continue
        existing = frappe.db.get_value("WAFD Hotel", {"hotel_name": hotel_name}, "name")
        doc = frappe.get_doc("WAFD Hotel", existing) if existing else frappe.new_doc("WAFD Hotel")
        if not existing:
            doc.hotel_name = hotel_name
            doc.status = "نشط / Active"
        # Normalize controlled Select values before assigning them.  The
        # geographic zone and the proximity band are intentionally separate:
        # a hotel outside the formal central area can still be within 2 km.
        zone_value = (row.get("zone_type") or "").strip()
        zone_aliases = {
            "قريب من المنطقة المركزية / Near Central": "خارج المنطقة المركزية / Outside Central Zone",
            "داخل المنطقة المركزية / Central Area": "المنطقة المركزية / Central Zone",
        }
        zone_value = zone_aliases.get(zone_value, zone_value)
        proximity_value = (row.get("proximity_band") or "").strip()

        meta = frappe.get_meta("WAFD Hotel")
        for fieldname, value in (
            ("zone_type", zone_value),
            ("proximity_band", proximity_value),
        ):
            if not value:
                continue
            field = meta.get_field(fieldname)
            allowed = [item.strip() for item in (field.options or "").splitlines() if item.strip()]
            if value not in allowed:
                frappe.log_error(
                    title="WAFD hotel catalogue Select normalization",
                    message=f"Skipped invalid {fieldname} value {value!r} for {hotel_name}. Allowed: {allowed}",
                )
                continue
            doc.set(fieldname, value)

        # Assign free-text fields directly.  Controlled Select fields are
        # normalized against the live DocType metadata before saving so a
        # catalogue label can never abort the site migration.
        for fieldname in ("hotel_name_en", "city", "district", "central_map_number", "central_sector", "source_map_edition", "source_authority", "source_url", "source_notes"):
            value = (row.get(fieldname) or "").strip()
            if value:
                doc.set(fieldname, value)

        verification_value = (row.get("verification_status") or "").strip()
        verification_aliases = {
            "تم التحقق من القرب / Proximity Verified": "يحتاج مراجعة / Needs Review",
            "موثق من المصدر الرسمي / Official Source Verified": "موثق من الموقع الرسمي للمنشأة / Official Property Source",
        }
        verification_value = verification_aliases.get(verification_value, verification_value)
        verification_field = meta.get_field("verification_status")
        verification_allowed = [
            item.strip() for item in (verification_field.options or "").splitlines() if item.strip()
        ]
        if verification_value in verification_allowed:
            doc.verification_status = verification_value
        elif verification_allowed:
            # Use the safest non-assertive status rather than failing migration.
            fallback = "يحتاج مراجعة / Needs Review"
            doc.verification_status = fallback if fallback in verification_allowed else verification_allowed[0]
            frappe.log_error(
                title="WAFD hotel verification status normalization",
                message=(
                    f"Normalized invalid verification_status {verification_value!r} "
                    f"for {hotel_name} to {doc.verification_status!r}. "
                    f"Allowed: {verification_allowed}"
                ),
            )
        if row.get("distance_to_haram_km") not in (None, ""):
            doc.distance_to_haram_km = float(row["distance_to_haram_km"])
        doc.last_verified_on = nowdate()
        doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)
        installed += 1
    return {"catalogue_count": len(rows), "installed_or_updated": installed}

def after_migrate():
    ensure_hotel_undertaking_print_format()
    ensure_madinah_hotels_400()
    ensure_madinah_central_and_nearby_hotels()
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
