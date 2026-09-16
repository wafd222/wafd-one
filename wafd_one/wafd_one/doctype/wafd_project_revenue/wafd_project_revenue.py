import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class WAFDProjectRevenue(Document):
    def validate(self):
        from wafd_one.governance import ensure_approved
        if self.status == "محصل / Collected" and not self.is_new():
            previous = self.get_doc_before_save()
            if previous and previous.status != self.status:
                ensure_approved(self, "تحصيل الإيراد / revenue collection")
        if flt(self.amount) <= 0:
            frappe.throw("يجب أن يكون مبلغ الإيراد أكبر من صفر / Revenue amount must be greater than zero")
        if self.revenue_date and getdate(self.revenue_date) > getdate(nowdate()):
            frappe.throw("لا يمكن تسجيل إيراد بتاريخ مستقبلي / Revenue date cannot be in the future")
        self._protect_collected_record()
        if self.status == "محصل / Collected" and self.payment_method in (None, "", "آجل / Credit"):
            frappe.throw("اختر طريقة تحصيل فعلية للإيراد المحصل / Select an actual payment method for collected revenue")

    def on_update(self):
        self._refresh_project()

    def on_trash(self):
        if self.status == "محصل / Collected":
            frappe.throw("لا يمكن حذف إيراد محصل / Collected revenue cannot be deleted")

    def after_delete(self):
        self._refresh_project()

    def _protect_collected_record(self):
        if self.is_new():
            return
        old = self.get_doc_before_save()
        if not old or old.status != "محصل / Collected":
            return
        protected = ("project", "revenue_date", "description", "amount", "payment_method", "reference_number", "attachment")
        changed = [field for field in protected if self.get(field) != old.get(field)]
        if changed or self.status != "محصل / Collected":
            frappe.throw("لا يمكن تعديل أو إلغاء إيراد محصل / Collected revenue cannot be changed or cancelled")

    def _refresh_project(self):
        if self.project:
            from wafd_one.finance import refresh_project_financials
            refresh_project_financials(self.project)
