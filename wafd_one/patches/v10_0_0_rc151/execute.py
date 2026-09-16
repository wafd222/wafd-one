"""RC151: make WAFD role permissions code-controlled and remove stale UI overrides."""
import frappe


def execute():
    # Role Permission Manager writes Custom DocPerm rows. Those rows can drift from
    # the app's shipped permission matrix and survive deployments. For WAFD-owned
    # doctypes, the application is the source of truth; clear stale overrides so
    # the JSON permissions synced by migrate are effective for every user/role.
    wafd_doctypes = frappe.get_all(
        "DocType",
        filters={"name": ["like", "WAFD %"]},
        pluck="name",
    )
    if wafd_doctypes:
        frappe.db.delete("Custom DocPerm", {"parent": ["in", wafd_doctypes]})

    frappe.clear_cache()
