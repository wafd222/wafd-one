import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt


class WAFDGovernanceSettings(Document):
    def validate(self):
        threshold_fields = (
            "contract_threshold",
            "purchase_threshold",
            "invoice_threshold",
            "payment_threshold",
            "cost_threshold",
            "revenue_threshold",
        )
        for fieldname in threshold_fields:
            if flt(self.get(fieldname)) < 0:
                frappe.throw(
                    "لا يمكن أن يكون حد الاعتماد سالبًا / Approval thresholds cannot be negative"
                )

        if cint(self.audit_retention_days) < 1:
            frappe.throw(
                "مدة الاحتفاظ بسجل التدقيق يجب أن تكون يومًا واحدًا على الأقل / Audit retention must be at least one day"
            )

        if not self.approver_role:
            self.approver_role = "WAFD Approver"
        if not frappe.db.exists("Role", self.approver_role):
            frappe.throw(
                "دور المعتمد غير موجود / The configured approver role does not exist"
            )
