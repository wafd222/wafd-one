"""RC160: Frappe v16 Workspace Sidebar navigation fix.

RC159 confirmed that DocType permissions alone are not sufficient to make a
custom operational DocType discoverable in the v16 Desk command palette.  In
v16, navigation is driven by ``Workspace Sidebar``; when a custom app has no
standard sidebar, Frappe auto-generates a module sidebar and deliberately keeps
only the first three DocTypes.  WAFD Production Batch therefore remained absent
from navigation even though its role permissions were correct.

This patch installs a curated standard WAFD ONE sidebar and repairs any stale
per-user WAFD ONE sidebar copy for Production Supervisors.  It changes no
projects, batches, invoices, payments or other operational records.
"""
from pathlib import Path
import json
import frappe

PRODUCTION_BATCH_PAGE = "wafd-production-batches"
PRODUCTION_BATCH_LABEL = "دفعات الإنتاج / WAFD Production Batch"
PAGE_ROLES = (
    "System Manager",
    "WAFD Operations Manager",
    "WAFD Production Supervisor",
    "WAFD Quality Inspector",
    "WAFD Project Manager",
    "WAFD Delivery Supervisor",
)


def _sidebar_source_path():
    return Path(frappe.get_app_path("wafd_one")) / "workspace_sidebar" / "wafd_one.json"


def _load_sidebar_items():
    source = json.loads(_sidebar_source_path().read_text(encoding="utf-8"))
    return source["items"]


def _sync_page_roles():
    frappe.reload_doc("wafd_one", "page", "wafd_production_batches", force=True)
    page = frappe.get_doc("Page", PRODUCTION_BATCH_PAGE)
    page.title = "WAFD Production Batch"
    page.set("roles", [{"role": role} for role in PAGE_ROLES if frappe.db.exists("Role", role)])
    page.flags.ignore_permissions = True
    page.flags.ignore_version = True
    page.save(ignore_permissions=True)


def _make_sidebar_doc(name="WAFD ONE"):
    if frappe.db.exists("Workspace Sidebar", name):
        sidebar = frappe.get_doc("Workspace Sidebar", name)
    else:
        sidebar = frappe.new_doc("Workspace Sidebar")
        sidebar.title = name

    sidebar.header_icon = "package"
    sidebar.module = "WAFD ONE"
    sidebar.standard = 1 if name == "WAFD ONE" else 0
    sidebar.app = "wafd_one" if name == "WAFD ONE" else None
    sidebar.set("items", [])
    for item in _load_sidebar_items():
        sidebar.append("items", item)
    sidebar.flags.ignore_permissions = True
    sidebar.flags.ignore_version = True
    if sidebar.is_new():
        sidebar.insert(ignore_permissions=True)
    else:
        sidebar.save(ignore_permissions=True)
    return sidebar


def _repair_production_supervisor_sidebar_copies():
    # A Desk user can acquire a private sidebar copy when customizing the v16
    # sidebar.  If such a stale copy exists it shadows the standard sidebar, so
    # update only Production Supervisor copies to the same curated links.
    production_users = frappe.get_all(
        "Has Role",
        filters={
            "parenttype": "User",
            "role": "WAFD Production Supervisor",
        },
        pluck="parent",
    )
    for user in production_users:
        candidates = frappe.get_all(
            "Workspace Sidebar",
            filters={"for_user": user},
            fields=["name", "title"],
        )
        for row in candidates:
            if not (row.name.startswith("WAFD ONE-") or row.title.startswith("WAFD ONE-")):
                continue
            sidebar = frappe.get_doc("Workspace Sidebar", row.name)
            sidebar.set("items", [])
            for item in _load_sidebar_items():
                sidebar.append("items", item)
            sidebar.flags.ignore_permissions = True
            sidebar.flags.ignore_version = True
            sidebar.save(ignore_permissions=True)


def _validate():
    sidebar = frappe.get_doc("Workspace Sidebar", "WAFD ONE")
    if not sidebar.standard or sidebar.app != "wafd_one":
        frappe.throw("RC160 failed to install the standard WAFD ONE Workspace Sidebar")

    matches = [
        row for row in sidebar.items
        if row.link_type == "Page" and row.link_to == PRODUCTION_BATCH_PAGE
    ]
    if len(matches) != 1 or "WAFD Production Batch" not in (matches[0].label or ""):
        frappe.throw("RC160 Production Batch sidebar navigation is missing")

    page_roles = set(frappe.get_all(
        "Has Role",
        filters={"parent": PRODUCTION_BATCH_PAGE, "parenttype": "Page"},
        pluck="role",
    ))
    if "WAFD Production Supervisor" not in page_roles:
        frappe.throw("RC160 Production Batch Page role is missing")

    perms = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": "WAFD Production Batch",
            "role": "WAFD Production Supervisor",
            "permlevel": 0,
        },
        fields=["read", "write", "create", "print", "report"],
        limit=1,
    )
    if not perms or not all(int(perms[0].get(k) or 0) for k in ("read", "write", "create", "print", "report")):
        frappe.throw("RC160 Production Supervisor Production Batch permissions are not active")


def execute():
    _sync_page_roles()
    _make_sidebar_doc()
    _repair_production_supervisor_sidebar_copies()
    _validate()

    # v16 caches sidebar/page/role data per user for hours; force the next Desk
    # session to rebuild navigation from the corrected sidebar and permissions.
    frappe.clear_cache()
