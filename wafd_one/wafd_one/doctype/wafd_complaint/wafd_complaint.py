import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

class WAFDComplaint(Document):
    def validate(self):
        if self.status == 'مغلقة' and not self.corrective_action:
            frappe.throw(_("Corrective Action is required before closing the complaint"))
        if self.status == 'مغلقة' and not self.closed_at:
            self.closed_at = now_datetime()
