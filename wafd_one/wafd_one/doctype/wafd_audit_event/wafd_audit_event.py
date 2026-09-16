import frappe
from frappe.model.document import Document


class WAFDAuditEvent(Document):
    def before_save(self):
        if not self.is_new():
            frappe.throw(
                "سجل التدقيق غير قابل للتعديل / Audit events are immutable"
            )

    def on_trash(self):
        frappe.throw(
            "لا يمكن حذف سجل التدقيق / Audit events cannot be deleted"
        )
