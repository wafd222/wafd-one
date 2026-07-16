import json
from pathlib import Path

import frappe


ROLES = [
    "WAFD Operations Manager", "WAFD Project Manager", "WAFD Production Supervisor",
    "WAFD Quality Inspector", "WAFD Delivery Supervisor", "WAFD Driver",
    "WAFD Finance User", "WAFD Storekeeper",
]


def ensure_roles():
    for role_name in ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)


def _workspace_definition():
    path = Path(__file__).resolve().parent / "wafd_one" / "workspace" / "wafd_one" / "wafd_one.json"
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _workspace_links_are_ready(data):
    """Return True only when every DocType referenced by the workspace exists.

    Workspace rows validate their Link To values on insert. During pre-model-sync
    patches those DocTypes may not exist yet, so workspace creation must be
    deferred until after the schema sync has completed.
    """
    referenced = set()
    for row in data.get("shortcuts", []):
        if row.get("type") == "DocType" and row.get("link_to"):
            referenced.add(row["link_to"])
    for row in data.get("links", []):
        if row.get("type") == "Link" and row.get("link_type") == "DocType" and row.get("link_to"):
            referenced.add(row["link_to"])
    return all(frappe.db.exists("DocType", doctype) for doctype in referenced)


def ensure_workspace(force_rebuild=False):
    data = _workspace_definition()
    if not _workspace_links_are_ready(data):
        frappe.log_error(
            "Workspace rebuild deferred until all linked WAFD ONE DocTypes are synchronized.",
            "WAFD ONE workspace setup deferred",
        )
        return False
    data.update({"type": "Workspace", "app": "wafd_one", "public": 1, "is_hidden": 0, "hide_custom": 0, "roles": []})
    name = data["name"]
    if force_rebuild and frappe.db.exists("Workspace", name):
        frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)
    if frappe.db.exists("Workspace", name):
        doc = frappe.get_doc("Workspace", name)
        for key, value in data.items():
            if key in {"doctype", "name", "creation", "modified", "modified_by", "owner", "idx", "docstatus"}:
                continue
            if doc.meta.has_field(key) and not isinstance(value, list):
                doc.set(key, value)
        for table_field in ("shortcuts", "links", "roles", "charts", "number_cards", "quick_lists", "custom_blocks"):
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
            settings.save()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "WAFD ONE default app setup")


def apply_setup(force_rebuild=False):
    ensure_roles()
    ensure_workspace(force_rebuild=force_rebuild)
    ensure_default_app()
    frappe.clear_cache()


def after_install():
    apply_setup(force_rebuild=True)


def after_migrate():
    apply_setup(force_rebuild=False)
