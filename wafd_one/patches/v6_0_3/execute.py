import frappe

from wafd_one.setup import ensure_roles


def execute():
    ensure_roles()
    for single in (
        "WAFD Operations Settings",
        "WAFD Food Safety Settings",
        "WAFD Governance Settings",
        "WAFD Print Settings",
        "WAFD Administration Console",
    ):
        if frappe.db.exists("DocType", single) and not frappe.db.exists(single, single):
            frappe.get_doc({"doctype": single}).insert(ignore_permissions=True)
    frappe.clear_cache()
