import frappe


def execute():
    for name in ("wafd_food_safety_settings", "wafd_ccp_check", "wafd_stock_movement_item", "wafd_production_batch"):
        frappe.reload_doc("wafd_one", "doctype", name, force=True, reset_permissions=True)
    settings = frappe.get_single("WAFD Food Safety Settings")
    settings.flags.ignore_permissions = True
    settings.save(ignore_permissions=True)
    batches = frappe.get_all("WAFD Production Batch", filters={"traceability_code": ["in", ["", None]]}, pluck="name")
    for batch_name in batches:
        doc = frappe.get_doc("WAFD Production Batch", batch_name)
        doc._ensure_traceability_code()
        doc.db_set("traceability_code", doc.traceability_code, update_modified=False)
