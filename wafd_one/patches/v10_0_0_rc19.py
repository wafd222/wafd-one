import frappe


def execute():
    # Re-save open production batches so derived quantities are refreshed safely.
    for name in frappe.get_all("WAFD Production Batch", pluck="name"):
        try:
            doc = frappe.get_doc("WAFD Production Batch", name)
            planned = frappe.utils.cint(doc.planned_quantity)
            produced = frappe.utils.cint(doc.produced_quantity)
            rejected = frappe.utils.cint(doc.rejected_quantity)
            frappe.db.set_value("WAFD Production Batch", name, {
                "remaining_quantity": max(planned - produced - rejected, 0),
                "completion_percent": (produced / planned * 100) if planned else 0,
            }, update_modified=False)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"RC19 production refresh failed: {name}")
