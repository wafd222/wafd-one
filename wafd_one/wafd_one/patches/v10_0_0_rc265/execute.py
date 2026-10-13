import frappe


def execute():
    """Install category-first entry and the cleaning handover workflow."""
    frappe.reload_doc("wafd_one", "doctype", "wafd_cleaning_material_usage_item", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_cleaning_material_usage", force=True, reset_permissions=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_stock_movement", force=True, reset_permissions=False)
    frappe.reload_doc("wafd_one", "page", "wafd_cleaning_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_storekeeper_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_role_home", force=True)
    frappe.clear_cache(doctype="WAFD Stock Movement")
    frappe.clear_cache(doctype="WAFD Cleaning Material Usage")
    frappe.clear_cache(doctype="Page")
