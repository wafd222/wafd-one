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


def ensure_workspace():
    data = _workspace_definition()
    name = data["name"]
    if frappe.db.exists("Workspace", name):
        doc = frappe.get_doc("Workspace", name)
        for field in (
            "title", "label", "module", "icon", "sequence_id", "public",
            "is_hidden", "hide_custom", "content", "parent_page", "for_user",
        ):
            if field in data:
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
        doc.save()
    else:
        doc = frappe.get_doc(data)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_version = True
        doc.insert()


def ensure_default_app():
    """Route system users directly to WAFD ONE after login.

    The field exists in Frappe v16. Guard all writes for compatibility.
    """
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
    ensure_workspace()
    ensure_default_app()
    frappe.clear_cache()


def after_install():
    apply_setup()


def after_migrate():
    apply_setup()
