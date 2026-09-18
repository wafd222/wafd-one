import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


LOCKED_STATUSES = {"معتمد / Approved", "مدفوع / Paid"}


class WAFDProjectCost(Document):
    def validate(self):
        from wafd_one.governance import ensure_approved
        if self.status in LOCKED_STATUSES and not self.is_new():
            previous = self.get_doc_before_save()
            if previous and previous.status != self.status:
                ensure_approved(self, "اعتماد التكلفة / cost approval")
        if flt(self.amount) <= 0:
            frappe.throw("يجب أن يكون مبلغ التكلفة أكبر من صفر / Cost amount must be greater than zero")
        if self.cost_date and getdate(self.cost_date) > getdate(nowdate()):
            frappe.throw("لا يمكن تسجيل تكلفة بتاريخ مستقبلي / Cost date cannot be in the future")
        self._protect_approved_record()
        if self.status in LOCKED_STATUSES and not self.approved_by:
            self.approved_by = frappe.session.user

    def on_update(self):
        self._refresh_project()

    def on_trash(self):
        if self.status in LOCKED_STATUSES:
            frappe.throw("لا يمكن حذف تكلفة معتمدة أو مدفوعة / Approved or paid cost cannot be deleted")

    def after_delete(self):
        self._refresh_project()

    def _protect_approved_record(self):
        if self.is_new():
            return
        old = self.get_doc_before_save()
        if not old or old.status not in LOCKED_STATUSES:
            return
        protected = ("project", "cost_date", "cost_category", "description", "supplier", "amount", "tax_included", "attachment")
        changed = [field for field in protected if self.get(field) != old.get(field)]
        if changed:
            frappe.throw("لا يمكن تعديل بيانات تكلفة معتمدة أو مدفوعة / Approved or paid cost details cannot be changed")
        if self.status not in LOCKED_STATUSES and self.status != "ملغي / Cancelled":
            frappe.throw("لا يمكن إعادة التكلفة المعتمدة إلى مسودة / Approved cost cannot be returned to draft")

    def _refresh_project(self):
        if self.project:
            from wafd_one.finance import refresh_project_financials
            refresh_project_financials(self.project)
