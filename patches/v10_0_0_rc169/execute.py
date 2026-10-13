import frappe


def execute():
    role_name = "WAFD Client Portal User"
    if not frappe.db.exists("Role", role_name):
        frappe.get_doc({"doctype":"Role", "role_name": role_name, "desk_access": 0}).insert(ignore_permissions=True)
    else:
        frappe.db.set_value("Role", role_name, "desk_access", 0, update_modified=False)

    # Standard DocTypes are synced by migrate before patches; this validation
    # makes a partial package fail clearly instead of silently exposing a broken portal.
    for doctype in ("WAFD Client Portal Access", "WAFD Client Receipt Acknowledgement"):
        if not frappe.db.exists("DocType", doctype):
            frappe.throw(f"RC169 portal metadata missing: {doctype}")
    frappe.clear_cache()
