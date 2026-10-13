"""Repair published Iftar employee assignments and refresh RC310 task screens."""

import frappe


CORE_ROLE_BY_FIELD = {
    "project_manager_user": "WAFD Project Manager",
    "kitchen_supervisor_user": "WAFD Iftar Kitchen Supervisor",
    "delivery_supervisor_user": "WAFD Delivery Supervisor",
    "site_manager_user": "WAFD Iftar Site Manager",
}


def _ensure_role(user, role, touched):
    user = (user or "").strip()
    if not user or not frappe.db.exists("User", {"name": user, "enabled": 1, "user_type": "System User"}):
        return
    if not frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": role}):
        doc = frappe.get_doc("User", user)
        doc.append("roles", {"role": role})
        doc.flags.ignore_permissions = True
        doc.save()
    touched.add(user)


def execute():
    for page in (
        "wafd_iftar_team",
        "wafd_role_home",
        "wafd_iftar_wizard",
        "wafd_iftar_operations",
    ):
        frappe.reload_doc("wafd_one", "page", page, force=True)

    touched = set()
    projects = frappe.get_all(
        "WAFD Iftar Project",
        filters={"docstatus": ["<", 2]},
        fields=["name", "docstatus", *CORE_ROLE_BY_FIELD],
        limit_page_length=2000,
    )
    for project in projects:
        for fieldname, role in CORE_ROLE_BY_FIELD.items():
            _ensure_role(project.get(fieldname), role, touched)

    for user in frappe.get_all(
        "WAFD Iftar Supervisor Plan",
        filters={"supervisor_user": ["is", "set"]},
        pluck="supervisor_user",
        limit_page_length=5000,
    ):
        _ensure_role(user, "WAFD Iftar Supervisor", touched)

    from wafd_one.wafd_one.iftar_pro import generate_daily_operations
    for project in projects:
        if int(project.docstatus or 0) == 1:
            generate_daily_operations(project.name, ignore_permissions=True)

    for user in touched:
        frappe.clear_cache(user=user)
    frappe.clear_cache()
