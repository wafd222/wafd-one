import frappe

def execute():
    for role in ("WAFD Undertaking Officer", "WAFD Undertaking Reviewer"):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype":"Role","role_name":role,"desk_access":1}).insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Role", role, "desk_access", 1, update_modified=False)
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True, reset_permissions=True)
    for row in frappe.get_all("WAFD Hotel Undertaking", fields=["name","owner","prepared_by_user","prepared_by_name"]):
        values={}
        if not row.prepared_by_user: values["prepared_by_user"] = row.owner
        if not row.prepared_by_name: values["prepared_by_name"] = frappe.db.get_value("User", row.owner, "full_name") or row.owner
        if values: frappe.db.set_value("WAFD Hotel Undertaking", row.name, values, update_modified=False)
    frappe.clear_cache(doctype="WAFD Hotel Undertaking")
