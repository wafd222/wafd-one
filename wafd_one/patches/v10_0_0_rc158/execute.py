"""RC158: role visibility repair for Desk search/sidebar.

Confirmed in the Production Supervisor smoke test after RC157:
- WAFD Production Batch did not appear in Awesomebar/Desk search even though
  the source DocType matrix grants the role read/write/create access.
- privileged WAFD pages were still listed in the Desk sidebar on an existing
  site because their Page metadata had not all been force-reloaded by RC157.

This patch makes the deployed database metadata authoritative again without
changing operational records or reopening completed projects.
"""
import frappe
from frappe.permissions import setup_custom_perms

RIGHTS = (
    "select", "read", "write", "create", "delete", "submit", "cancel",
    "amend", "print", "email", "report", "import", "export", "share",
)

PRODUCTION_BATCH_MATRIX = {
    "System Manager": {"read":1,"write":1,"create":1,"delete":1,"print":1,"email":1,"report":1,"export":1,"share":1},
    "WAFD Operations Manager": {"read":1,"write":1,"create":1,"print":1,"email":1,"report":1,"export":1,"share":1},
    "WAFD Production Supervisor": {"read":1,"write":1,"create":1,"print":1,"report":1,"select":1},
    "WAFD Quality Inspector": {"read":1,"print":1,"report":1,"select":1},
    "WAFD Project Manager": {"read":1,"print":1,"report":1,"select":1},
    "WAFD Delivery Supervisor": {"read":1,"print":1,"report":1,"select":1},
}

# These pages must never be exposed to production/quality/store/delivery users.
PAGE_ROLE_MATRIX = {
    "wafd_administration_console": ("System Manager", "WAFD Operations Manager"),
    "wafd_document_studio": ("System Manager", "WAFD Operations Manager", "WAFD Project Manager"),
    "wafd_launch_center": ("System Manager", "WAFD Operations Manager"),
    "wafd_one_dashboard": ("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Finance User", "WAFD Approver", "WAFD Auditor"),
    "wafd_iftar_wizard": ("System Manager", "WAFD Operations Manager", "WAFD Project Manager"),
    "wafd_iftar_operations": ("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Delivery Supervisor", "WAFD Storekeeper"),
    "wafd_iftar_report_center": ("System Manager", "WAFD Operations Manager", "WAFD Project Manager", "WAFD Auditor"),
}


def _enforce_production_batch_permissions():
    frappe.reload_doc("wafd_one", "doctype", "wafd_production_batch", force=True, reset_permissions=True)

    # Remove stale site-level overrides, then publish one exact matrix.  Using
    # Custom DocPerm intentionally makes the permissions deterministic on sites
    # that accumulated manual Role Permission Manager edits during testing.
    setup_custom_perms("WAFD Production Batch")
    frappe.db.delete("Custom DocPerm", {"parent": "WAFD Production Batch"})
    for role, grants in PRODUCTION_BATCH_MATRIX.items():
        if not frappe.db.exists("Role", role):
            continue
        row = frappe.get_doc({
            "doctype": "Custom DocPerm",
            "parent": "WAFD Production Batch",
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": role,
            "permlevel": 0,
        })
        for right in RIGHTS:
            row.set(right, int(grants.get(right, 0)))
        row.insert(ignore_permissions=True)


def _reload_page_metadata():
    for page_file, allowed_roles in PAGE_ROLE_MATRIX.items():
        page_name = page_file.replace("_", "-")
        try:
            frappe.reload_doc("wafd_one", "page", page_file, force=True)
        except Exception:
            # Keep migrate resilient only when an optional page genuinely does
            # not exist on the target site.
            if frappe.db.exists("Page", page_name):
                raise
            continue

        if frappe.db.exists("Page", page_name):
            page = frappe.get_doc("Page", page_name)
            page.set("roles", [{"role": role} for role in allowed_roles if frappe.db.exists("Role", role)])
            page.flags.ignore_permissions = True
            page.save(ignore_permissions=True)


def execute():
    from wafd_one.setup import rebuild_workspace_from_source

    _enforce_production_batch_permissions()
    _reload_page_metadata()
    rebuild_workspace_from_source()

    # Permission, Page and Workspace metadata are cached per user.  Clearing
    # the global cache is required so the next login/search reflects RC158.
    frappe.clear_cache()
