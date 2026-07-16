import json
from pathlib import Path

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

PHASE_ONE_DOCTYPES = (
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


def ensure_system_manager_access():
    """Give existing System Managers access to WAFD ONE Phase 1.

    This avoids a workspace that shows headings but hides every shortcut because
    the logged-in administrator does not yet have a WAFD-specific role.
    """
    users = frappe.get_all(
        "Has Role",
        filters={"role": "System Manager", "parenttype": "User"},
        pluck="parent",
    )
    for user_name in users:
        if user_name == "Guest" or not frappe.db.get_value("User", user_name, "enabled"):
            continue
        user = frappe.get_doc("User", user_name)
        current_roles = {row.role for row in user.roles}
        if "WAFD Operations Manager" not in current_roles:
            user.append("roles", {"role": "WAFD Operations Manager"})
            user.flags.ignore_permissions = True
            user.flags.ignore_version = True
            user.save()


def _workspace_definition():
    path = (
        Path(__file__).resolve().parent
        / "wafd_one"
        / "workspace"
        / "wafd_one"
        / "wafd_one.json"
    )
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _workspace_links_are_ready(data):
    referenced = set()
    for row in data.get("shortcuts", []):
        if row.get("type") == "DocType" and row.get("link_to"):
            referenced.add(row["link_to"])
    for row in data.get("links", []):
        if (
            row.get("type") == "Link"
            and row.get("link_type") == "DocType"
            and row.get("link_to")
        ):
            referenced.add(row["link_to"])
    return all(frappe.db.exists("DocType", doctype) for doctype in referenced)


def ensure_workspace(force_rebuild=False):
    data = _workspace_definition()
    if not _workspace_links_are_ready(data):
        missing = [
            doctype
            for doctype in PHASE_ONE_DOCTYPES
            if not frappe.db.exists("DocType", doctype)
        ]
        frappe.log_error(
            f"Workspace rebuild deferred. Missing DocTypes: {', '.join(missing)}",
            "WAFD ONE workspace setup deferred",
        )
        return False

    data.update(
        {
            "doctype": "Workspace",
            "app": "wafd_one",
            "public": 1,
            "is_hidden": 0,
            "hide_custom": 0,
            "roles": [],
        }
    )
    name = data["name"]

    if force_rebuild and frappe.db.exists("Workspace", name):
        frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)

    if frappe.db.exists("Workspace", name):
        doc = frappe.get_doc("Workspace", name)
        protected = {
            "doctype",
            "name",
            "creation",
            "modified",
            "modified_by",
            "owner",
            "idx",
            "docstatus",
        }
        for key, value in data.items():
            if key not in protected and doc.meta.has_field(key) and not isinstance(value, list):
                doc.set(key, value)

        table_fields = (
            "shortcuts",
            "links",
            "roles",
            "charts",
            "number_cards",
            "quick_lists",
            "custom_blocks",
        )
        for table_field in table_fields:
            if doc.meta.has_field(table_field):
                doc.set(table_field, [])
                for row in data.get(table_field, []):
                    doc.append(table_field, row)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_version = True
        doc.save()
    else:
        doc = frappe.get_doc(data)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_version = True
        doc.insert()

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


def apply_setup(force_rebuild=False, assign_manager_access=False):
    ensure_roles()
    if assign_manager_access:
        ensure_system_manager_access()
    ensure_workspace(force_rebuild=force_rebuild)
    ensure_default_app()
    frappe.clear_cache()


def after_install():
    apply_setup(force_rebuild=True, assign_manager_access=True)


def after_migrate():
    apply_setup(force_rebuild=False, assign_manager_access=True)
