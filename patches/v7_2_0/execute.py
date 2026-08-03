import frappe

def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_costing_settings")
    frappe.reload_doc("wafd_one", "doctype", "wafd_cost_snapshot")
    if frappe.db.exists("DocType", "WAFD Costing Settings"):
        doc = frappe.get_single("WAFD Costing Settings")
        if doc.is_new():
            doc.insert(ignore_permissions=True)
