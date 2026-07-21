import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class WAFDPayment(Document):
    def validate(self):
        from wafd_one.governance import approval_required, ensure_approved
        if self.status == "معتمد / Confirmed":
            if self.is_new() and approval_required(self):
                frappe.throw(
                    "احفظ التحصيل كمسودة أولاً ثم أنشئ طلب اعتماد / "
                    "Save the payment as a draft before requesting approval"
                )
            if not self.is_new():
                previous = self.get_doc_before_save()
                if previous and previous.status != self.status:
                    ensure_approved(self, "اعتماد التحصيل / payment confirmation")
        if not self.payment_date:
            self.payment_date = nowdate()
        if not self.invoice:
            frappe.throw("الفاتورة مطلوبة / Invoice is required")

        self._protect_confirmed_payment()

        from wafd_one.finance import get_invoice_totals

        totals = get_invoice_totals(self.invoice, exclude_payment=self.name if not self.is_new() else None)
        self.project = totals["project"]
        self.invoice_total = totals["invoice_total"]
        self.previously_paid = totals["paid_amount"]
        self.outstanding_before = totals["balance"]

        invoice_date = frappe.db.get_value("WAFD Invoice", self.invoice, "invoice_date")
        if invoice_date and getdate(self.payment_date) < getdate(invoice_date):
            frappe.throw("تاريخ التحصيل لا يمكن أن يسبق تاريخ الفاتورة / Payment date cannot precede invoice date")
        if totals["status"] == "ملغاة / Cancelled":
            frappe.throw("لا يمكن تسجيل تحصيل على فاتورة ملغاة / Cannot pay a cancelled invoice")
        if flt(self.invoice_total) <= 0:
            frappe.throw("لا يمكن تسجيل تحصيل لفاتورة قيمتها صفر / Cannot pay a zero-value invoice")
        if flt(self.amount) <= 0:
            frappe.throw("مبلغ التحصيل يجب أن يكون أكبر من صفر / Payment must be greater than zero")
        if self.status == "معتمد / Confirmed" and flt(self.amount) > flt(self.outstanding_before):
            frappe.throw(
                "مبلغ التحصيل يتجاوز الرصيد المتبقي ({0}) / Payment exceeds outstanding balance ({0})".format(
                    frappe.format_value(self.outstanding_before, {"fieldtype": "Currency"})
                )
            )

    def _protect_confirmed_payment(self):
        if self.is_new():
            return
        previous = self.get_doc_before_save()
        if not previous or previous.status != "معتمد / Confirmed":
            return
        protected = ("invoice", "project", "amount", "payment_date", "payment_method", "reference_number")
        changed = [self.meta.get_label(field) for field in protected if self.get(field) != previous.get(field)]
        if changed:
            frappe.throw(
                "لا يمكن تعديل بيانات تحصيل معتمد: {0} / Confirmed payment fields cannot be changed: {0}".format(
                    ", ".join(changed)
                )
            )
        if self.status != "معتمد / Confirmed":
            frappe.throw("لا يمكن تغيير حالة تحصيل معتمد. أنشئ قيد إلغاء مستقل / A confirmed payment cannot be reopened or cancelled by editing")

    def on_update(self):
        from wafd_one.finance import refresh_invoice_and_project
        refresh_invoice_and_project(self.invoice)

    def on_trash(self):
        if self.status == "معتمد / Confirmed":
            frappe.throw("لا يمكن حذف تحصيل معتمد / A confirmed payment cannot be deleted")
        frappe.enqueue(
            "wafd_one.finance.refresh_invoice_and_project",
            invoice_name=self.invoice,
            enqueue_after_commit=True,
        )
