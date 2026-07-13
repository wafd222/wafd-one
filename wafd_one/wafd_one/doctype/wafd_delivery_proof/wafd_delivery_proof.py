import frappe
from frappe.model.document import Document
from frappe.utils import cint

class WafdDeliveryProof(Document):
    def validate(self):
        if cint(self.received_quantity) < 0 or cint(self.rejected_quantity) < 0:
            frappe.throw("الكميات لا يمكن أن تكون سالبة")
