import frappe
from frappe.model.document import Document

class WAFDUndertakingBeneficiary(Document):
    def validate(self):
        self.beneficiary_name = (self.beneficiary_name or "").strip()
        if not self.beneficiary_name:
            frappe.throw("اسم المستفيد مطلوب / Beneficiary name is required")
