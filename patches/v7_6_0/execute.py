import frappe


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_operations_alert", force=True)
    # Ensure traceability identifiers exist for legacy production batches.
    if frappe.db.exists("DocType", "WAFD Production Batch"):
        rows = frappe.get_all("WAFD Production Batch", filters={"traceability_code": ["is", "not set"]}, pluck="name")
        for name in rows:
            doc = frappe.get_doc("WAFD Production Batch", name)
            doc._ensure_traceability_code()
            frappe.db.set_value("WAFD Production Batch", name, "traceability_code", doc.traceability_code, update_modified=False)
