from __future__ import annotations

import frappe


MANAGERS = {"System Manager", "WAFD Operations Manager"}


def _roles(user=None):
    return set(frappe.get_roles(user or frappe.session.user))


def _manager(user=None):
    return bool(_roles(user) & MANAGERS)


def _project_condition(user=None):
    user = user or frappe.session.user
    roles = _roles(user)
    if roles & MANAGERS:
        return ""
    escaped = frappe.db.escape(user)
    fields = []
    if "WAFD Project Manager" in roles:
        fields.append("project_manager_user")
    if roles & {"WAFD Iftar Kitchen Supervisor", "WAFD Production Supervisor"}:
        fields.append("kitchen_supervisor_user")
    if "WAFD Delivery Supervisor" in roles:
        fields.append("delivery_supervisor_user")
    if "WAFD Iftar Site Manager" in roles:
        fields.append("site_manager_user")
    direct = " or ".join(f"`tabWAFD Iftar Project`.`{field}`={escaped}" for field in fields)
    supervisor = "exists (select 1 from `tabWAFD Iftar Supervisor Plan` sp where sp.project=`tabWAFD Iftar Project`.name and sp.supervisor_user={0})".format(escaped)
    return f"({direct} or {supervisor})" if direct else supervisor


def project_query(user=None):
    return _project_condition(user)


def project_has_permission(doc, user=None, permission_type=None):
    if _manager(user):
        return None
    user = user or frappe.session.user
    if user in {doc.project_manager_user, doc.kitchen_supervisor_user, doc.delivery_supervisor_user, doc.site_manager_user}:
        return True
    return bool(frappe.db.exists("WAFD Iftar Supervisor Plan", {"project": doc.name, "supervisor_user": user}))


def daily_query(user=None):
    condition = _project_condition(user)
    if not condition:
        return ""
    return "exists (select 1 from `tabWAFD Iftar Project` where `tabWAFD Iftar Project`.name=`tabWAFD Iftar Daily Operation`.project and {0})".format(condition)


def daily_has_permission(doc, user=None, permission_type=None):
    if _manager(user):
        return None
    project = frappe.get_doc("WAFD Iftar Project", doc.project)
    return project_has_permission(project, user, permission_type)


def plan_query(user=None):
    if _manager(user):
        return ""
    roles = _roles(user)
    if roles & {"WAFD Iftar Site Manager", "WAFD Project Manager"}:
        field = "site_manager_user" if "WAFD Iftar Site Manager" in roles else "project_manager_user"
        escaped = frappe.db.escape(user or frappe.session.user)
        return "exists (select 1 from `tabWAFD Iftar Project` p where p.name=`tabWAFD Iftar Supervisor Plan`.project and p.`{0}`={1})".format(field, escaped)
    return "`tabWAFD Iftar Supervisor Plan`.`supervisor_user`={0}".format(frappe.db.escape(user or frappe.session.user))


def plan_has_permission(doc, user=None, permission_type=None):
    if _manager(user):
        return None
    roles = _roles(user)
    if roles & {"WAFD Iftar Site Manager", "WAFD Project Manager"}:
        project = frappe.get_doc("WAFD Iftar Project", doc.project)
        return project_has_permission(project, user, permission_type)
    return doc.supervisor_user == (user or frappe.session.user)


def report_query(user=None):
    if _manager(user):
        return ""
    roles = _roles(user)
    if roles & {"WAFD Iftar Site Manager", "WAFD Project Manager"}:
        field = "site_manager_user" if "WAFD Iftar Site Manager" in roles else "project_manager_user"
        escaped = frappe.db.escape(user or frappe.session.user)
        return "exists (select 1 from `tabWAFD Iftar Project` p where p.name=`tabWAFD Iftar Supervisor Daily Report`.project and p.`{0}`={1})".format(field, escaped)
    return "`tabWAFD Iftar Supervisor Daily Report`.`supervisor_user`={0}".format(frappe.db.escape(user or frappe.session.user))


def report_has_permission(doc, user=None, permission_type=None):
    if _manager(user):
        return None
    if _roles(user) & {"WAFD Iftar Site Manager", "WAFD Project Manager"}:
        project = frappe.get_doc("WAFD Iftar Project", doc.project)
        return project_has_permission(project, user, permission_type)
    return doc.supervisor_user == (user or frappe.session.user)
