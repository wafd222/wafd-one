"""RC152: comprehensive role-permission baseline for all WAFD users.

WAFD-owned DocTypes are reloaded from source JSON and stale Custom DocPerm rows
are removed. A small, explicit set of ERPNext/Frappe master DocTypes is granted
read/select access where WAFD operational roles need lookup visibility.
"""
import frappe

WAFD_ROLES = (
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

STANDARD_LOOKUP_POLICY = {
    "Item": {
        "WAFD Operations Manager": {"read": 1, "select": 1, "write": 1, "create": 1, "print": 1, "report": 1},
        "WAFD Storekeeper": {"read": 1, "select": 1, "print": 1, "report": 1},
        "WAFD Production Supervisor": {"read": 1, "select": 1, "print": 1, "report": 1},
        "WAFD Finance User": {"read": 1, "select": 1, "report": 1},
    },
    "Item Group": {
        "WAFD Operations Manager": {"read": 1, "select": 1},
        "WAFD Storekeeper": {"read": 1, "select": 1},
        "WAFD Production Supervisor": {"read": 1, "select": 1},
    },
    "UOM": {
        "WAFD Operations Manager": {"read": 1, "select": 1},
        "WAFD Storekeeper": {"read": 1, "select": 1},
        "WAFD Production Supervisor": {"read": 1, "select": 1},
        "WAFD Finance User": {"read": 1, "select": 1},
    },
    "Warehouse": {
        "WAFD Operations Manager": {"read": 1, "select": 1},
        "WAFD Storekeeper": {"read": 1, "select": 1, "report": 1},
        "WAFD Production Supervisor": {"read": 1, "select": 1},
    },
}

RIGHTS = ("select", "read", "write", "create", "delete", "submit", "cancel", "amend", "print", "email", "report", "import", "export", "share")


def _replace_wafd_custom_permissions():
    wafd_doctypes = frappe.get_all("DocType", filters={"name": ["like", "WAFD %"]}, pluck="name")
    if wafd_doctypes:
        frappe.db.delete("Custom DocPerm", {"parent": ["in", wafd_doctypes]})


def _reload_wafd_doctypes():
    from wafd_one.setup import ALL_DOCTYPE_FILES
    for doctype_file in ALL_DOCTYPE_FILES:
        frappe.reload_doc("wafd_one", "doctype", doctype_file, force=True, reset_permissions=True)


def _set_standard_lookup_permissions():
    from frappe.permissions import setup_custom_perms
    for doctype, role_map in STANDARD_LOOKUP_POLICY.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        # Custom DocPerm overrides the standard permission table for a DocType.
        # Seed it with all existing standard rows first so ERPNext's native roles
        # are never lost, then replace only the WAFD-specific rows.
        setup_custom_perms(doctype)
        frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": ["in", list(WAFD_ROLES)]})
        for role, grants in role_map.items():
            row = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": doctype,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "permlevel": 0,
            })
            for right in RIGHTS:
                row.set(right, int(grants.get(right, 0)))
            row.insert(ignore_permissions=True)


def _reload_permissioned_pages():
    for page in (
        "wafd_one_dashboard",
        "wafd_iftar_wizard",
        "wafd_iftar_operations",
        "wafd_iftar_report_center",
        "wafd_launch_center",
        "wafd_administration_console",
        "wafd_document_studio",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)


def execute():
    _replace_wafd_custom_permissions()
    _reload_wafd_doctypes()
    _set_standard_lookup_permissions()
    _reload_permissioned_pages()
    frappe.clear_cache()
