"""RC159: Production Batch Desk/Awesomebar visibility hardening.

RC158 correctly removed restricted Pages, but the Production Supervisor smoke
check still could not discover ``WAFD Production Batch`` from Ctrl+K.  The
operational DocType itself remains the source of truth; this patch makes all
three navigation layers deterministic on existing sites:

1. synchronize the DocType and exact role permissions,
2. expose a role-restricted Desk Page whose title is ``WAFD Production Batch``
   and redirects to the real List view,
3. render the existing Production Batch shortcut in the WAFD ONE workspace.

No project, batch, invoice, payment or historical operational row is changed.
"""
import frappe
from frappe.permissions import setup_custom_perms

RIGHTS = (
    "select", "read", "write", "create", "delete", "submit", "cancel",
    "amend", "print", "email", "report", "import", "export", "share",
)

PRODUCTION_BATCH_MATRIX = {
    "System Manager": {"read":1,"write":1,"create":1,"delete":1,"print":1,"email":1,"report":1,"export":1,"share":1,"select":1},
    "WAFD Operations Manager": {"read":1,"write":1,"create":1,"print":1,"email":1,"report":1,"export":1,"share":1,"select":1},
    "WAFD Production Supervisor": {"read":1,"write":1,"create":1,"print":1,"report":1,"select":1},
    "WAFD Quality Inspector": {"read":1,"print":1,"report":1,"select":1},
    "WAFD Project Manager": {"read":1,"print":1,"report":1,"select":1},
    "WAFD Delivery Supervisor": {"read":1,"print":1,"report":1,"select":1},
}

SEARCH_PAGE_ROLES = (
    "System Manager",
    "WAFD Operations Manager",
    "WAFD Production Supervisor",
)


def _enforce_production_batch_permissions():
    frappe.reload_doc(
        "wafd_one", "doctype", "wafd_production_batch",
        force=True, reset_permissions=True,
    )

    # Existing test sites accumulated Role Permission Manager edits.  Keep one
    # authoritative Custom DocPerm matrix so current sites and fresh sites are
    # evaluated identically after this deployment.
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


def _ensure_desk_search_role():
    # Frappe Desk roles may carry a dedicated search_bar flag in addition to
    # desk_access.  Normalize it when the current Frappe schema provides it.
    for role in SEARCH_PAGE_ROLES:
        if not frappe.db.exists("Role", role):
            continue
        values = {"desk_access": 1}
        if frappe.db.has_column("Role", "search_bar"):
            values["search_bar"] = 1
        frappe.db.set_value("Role", role, values, update_modified=False)


def _install_search_route_page():
    frappe.reload_doc("wafd_one", "page", "wafd_production_batches", force=True)
    page_name = "wafd-production-batches"
    if not frappe.db.exists("Page", page_name):
        frappe.throw("RC159 failed to install the Production Batch Desk search route")

    page = frappe.get_doc("Page", page_name)
    page.title = "WAFD Production Batch"
    page.set(
        "roles",
        [{"role": role} for role in SEARCH_PAGE_ROLES if frappe.db.exists("Role", role)],
    )
    page.flags.ignore_permissions = True
    page.flags.ignore_version = True
    page.save(ignore_permissions=True)


def _validate_runtime_state():
    custom = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": "WAFD Production Batch",
            "role": "WAFD Production Supervisor",
            "permlevel": 0,
        },
        fields=["read", "write", "create", "select", "print", "report"],
        limit=1,
    )
    if not custom or not all(int(custom[0].get(key) or 0) for key in ("read", "write", "create", "select", "print", "report")):
        frappe.throw("RC159 Production Supervisor permission matrix did not persist")

    page_roles = set(
        frappe.get_all(
            "Has Role",
            filters={"parent": "wafd-production-batches", "parenttype": "Page"},
            pluck="role",
        )
    )
    if "WAFD Production Supervisor" not in page_roles:
        frappe.throw("RC159 Production Batch search Page role did not persist")

    workspace = frappe.get_doc("Workspace", "WAFD ONE")
    labels = {row.label: row.link_to for row in workspace.shortcuts}
    if labels.get("دفعات الإنتاج") != "WAFD Production Batch":
        frappe.throw("RC159 Production Batch workspace shortcut is missing")

    import json
    content = json.loads(workspace.content or "[]")
    if not any(
        row.get("type") == "shortcut"
        and row.get("data", {}).get("shortcut_name") == "دفعات الإنتاج"
        for row in content
    ):
        frappe.throw("RC159 Production Batch workspace block is not rendered")


def execute():
    from wafd_one.setup import rebuild_workspace_from_source

    _enforce_production_batch_permissions()
    _ensure_desk_search_role()
    _install_search_route_page()
    rebuild_workspace_from_source()
    _validate_runtime_state()

    # Boot/permission/workspace/Page route data are cached per Desk session.
    frappe.clear_cache(doctype="WAFD Production Batch")
    frappe.clear_cache()
