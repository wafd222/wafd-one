"""RC224: restore Undertaking Officer hotel-create permission deterministically."""
import frappe


def execute():
    if not frappe.db.exists("DocType", "WAFD Hotel"):
        return
    # A site may still carry a Custom DocPerm created by Role Permission Manager.
    # Remove only the Undertaking Officer override, then restore the source JSON
    # permission matrix (read/select/create, but no write/delete on existing hotels).
    frappe.db.delete("Custom DocPerm", {
        "parent": "WAFD Hotel",
        "role": "WAFD Undertaking Officer",
    })
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True, reset_permissions=True)
    frappe.clear_cache(doctype="WAFD Hotel")
    frappe.clear_cache()
