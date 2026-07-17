import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class WAFDPayment(Document):
    def validate(self):
        if not self.payment_date:
            self.payment_date = nowdate()
        if not self.invoice:
            frappe.throw("الفاتورة مطلوبة / Invoice is required")

        from wafd_one.finance import get_invoice_totals

        totals = get_invoice_totals(self.invoice, exclude_payment=self.name if not self.is_new() else None)
        self.project = totals["project"]
        self.invoice_total = totals["invoice_total"]
        self.previously_paid = totals["paid_amount"]
        self.outstanding_before = totals["balance"]

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

    def on_update(self):
        from wafd_one.finance import refresh_invoice_and_project
        refresh_invoice_and_project(self.invoice)

    def on_trash(self):
        frappe.enqueue(
            "wafd_one.finance.refresh_invoice_and_project",
            invoice_name=self.invoice,
            enqueue_after_commit=True,
        )
