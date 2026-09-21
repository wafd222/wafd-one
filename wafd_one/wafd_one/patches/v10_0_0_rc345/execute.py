"""Refresh only Iftar and Employee Management metadata changed by RC345."""

import frappe


SUPERVISOR_ROLE = "WAFD Iftar Supervisor"


def _ensure_existing_supervisors_keep_access():
    """Backfill the dedicated role for already assigned Iftar supervisors."""
    users = frappe.get_all(
        "WAFD Iftar Supervisor Plan",
        filters={"active": 1, "supervisor_user": ["is", "set"]},
        pluck="supervisor_user",
        limit_page_length=5000,
    )
    for user in sorted(set(users)):
        if not frappe.db.exists("User", {"name": user, "enabled": 1}):
            continue
        roles = set(frappe.get_roles(user))
        if SUPERVISOR_ROLE in roles or roles & {"System Manager", "WAFD Operations Manager"}:
            continue
        doc = frappe.get_doc("User", user)
        doc.append("roles", {"role": SUPERVISOR_ROLE})
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
        frappe.clear_cache(user=user)


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_iftar_project", force=True)
    for page in ("wafd_employee_team", "wafd_iftar_team", "wafd_iftar_site"):
        frappe.reload_doc("wafd_one", "page", page, force=True)
    _ensure_existing_supervisors_keep_access()
    frappe.clear_cache()
