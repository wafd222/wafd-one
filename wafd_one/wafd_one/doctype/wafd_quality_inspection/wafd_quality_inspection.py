import frappe
from frappe.model.document import Document


class WafdQualityInspection(Document):
    def on_update(self):
        if not self.production_batch:
            return
        mapping = {
            "ناجح / Passed": "ناجح / Passed",
            "مشروط / Conditional": "مشروط / Conditional",
            "مرفوض / Rejected": "مرفوض / Rejected",
        }
        frappe.db.set_value(
            "WAFD Production Batch",
            self.production_batch,
            "quality_status",
            mapping.get(self.result, "لم يفحص / Not Inspected"),
            update_modified=False,
        )
        if self.result == "مرفوض / Rejected":
            frappe.db.set_value("WAFD Production Batch", self.production_batch, "status", "موقوف / Stopped", update_modified=False)
