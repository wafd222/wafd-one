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


def ensure_roles():
    for role_name in ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)


def _workspace_definition():
    path = Path(__file__).resolve().parent / "wafd_one" / "workspace" / "wafd_one" / "wafd_one.json"
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _manual_workspace_sync(data):
    """Fallback sync for hosts where reload_doc cannot load Workspace exports."""
    name = data["name"]
    if frappe.db.exists("Workspace", name):
        doc = frappe.get_doc("Workspace", name)
    else:
        doc = frappe.new_doc("Workspace")
        doc.name = name

    for field in (
        "title", "label", "module", "app", "type", "icon", "sequence_id", "public",
        "is_hidden", "hide_custom", "content", "parent_page", "for_user",
    ):
        if field in data and doc.meta.has_field(field):
            doc.set(field, data[field])

    for table_field in (
        "shortcuts", "links", "roles", "charts", "number_cards",
        "quick_lists", "custom_blocks",
    ):
        if doc.meta.has_field(table_field):
            doc.set(table_field, [])
            for row in data.get(table_field, []):
                doc.append(table_field, row)

    doc.flags.ignore_permissions = True
    doc.flags.ignore_version = True
    if doc.is_new():
        doc.insert()
    else:
        doc.save()


def ensure_workspace(force_reload=False):
    """Install or refresh the standard WAFD ONE workspace.

    Frappe's standard-document loader is used first because it correctly
    rebuilds Workspace child tables and layout content on existing sites.
    A manual sync remains as a safe fallback.
    """
    data = _workspace_definition()
    data["type"] = "Workspace"
    data["app"] = data.get("app") or "wafd_one"

    reloaded = False
    try:
        frappe.reload_doc(
            "wafd_one",
            "workspace",
            "wafd_one",
            force=bool(force_reload),
            reset_permissions=True,
        )
        reloaded = frappe.db.exists("Workspace", data["name"])
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WAFD ONE standard workspace reload")

    if not reloaded:
        _manual_workspace_sync(data)
    else:
        # Keep these routing fields explicit after reload for Frappe Cloud v16.
        frappe.db.set_value(
            "Workspace",
            data["name"],
            {
                "app": "wafd_one",
                "module": "WAFD ONE",
                "public": 1,
                "is_hidden": 0,
                "hide_custom": 0,
            },
            update_modified=False,
        )

    frappe.clear_document_cache("Workspace", data["name"])


def ensure_default_app():
    """Route system users directly to WAFD ONE after login."""
    try:
        system_settings = frappe.get_single("System Settings")
        if system_settings.meta.has_field("default_app"):
            system_settings.default_app = "wafd_one"
            system_settings.flags.ignore_permissions = True
            system_settings.flags.ignore_version = True
            system_settings.save()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WAFD ONE default app setup")

    try:
        if frappe.db.exists("User", "Administrator"):
            user = frappe.get_doc("User", "Administrator")
            if user.meta.has_field("default_app"):
                user.default_app = "wafd_one"
                user.flags.ignore_permissions = True
                user.flags.ignore_version = True
                user.save()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WAFD ONE Administrator default app setup")


def apply_setup():
    ensure_roles()
    ensure_workspace(force_reload=True)
    ensure_default_app()
    frappe.clear_cache()


def after_install():
    apply_setup()


def after_migrate():
    apply_setup()
