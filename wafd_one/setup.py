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
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": 1,
                }
            ).insert(ignore_permissions=True)


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


def ensure_workspace():
    """Create or fully synchronize the standard workspace after migrations."""
    data = _workspace_definition()
    name = data["name"]

    if frappe.db.exists("Workspace", name):
        doc = frappe.get_doc("Workspace", name)
        for field in (
            "title",
            "label",
            "module",
            "icon",
            "sequence_id",
            "public",
            "is_hidden",
            "hide_custom",
            "content",
            "parent_page",
            "for_user",
        ):
            if field in data:
                doc.set(field, data[field])

        for table_field in ("shortcuts", "links", "roles", "charts", "number_cards", "quick_lists", "custom_blocks"):
            if doc.meta.has_field(table_field):
                doc.set(table_field, [])
                for row in data.get(table_field, []):
                    doc.append(table_field, row)
        doc.flags.ignore_permissions = True
        doc.save()
    else:
        doc = frappe.get_doc(data)
        doc.flags.ignore_permissions = True
        doc.insert()


def after_install():
    ensure_roles()
    ensure_workspace()
    frappe.clear_cache()


def after_migrate():
    ensure_roles()
    ensure_workspace()
    frappe.clear_cache()
