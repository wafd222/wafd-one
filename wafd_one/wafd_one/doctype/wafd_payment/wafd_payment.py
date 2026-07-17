import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class WAFDPayment(Document):
    def validate(self):
        if not self.payment_date:
            self.payment_date = nowdate()
        invoice = frappe.get_doc("WAFD Invoice", self.invoice)
        self.project = invoice.project
        if flt(self.amount) <= 0:
            frappe.throw("مبلغ التحصيل يجب أن يكون أكبر من صفر / Payment must be greater than zero")
        other = frappe.db.sql("""select coalesce(sum(amount),0) from `tabWAFD Payment` where invoice=%s and status='معتمد / Confirmed' and name!=%s""", (self.invoice, self.name or ""))[0][0]
        if self.status == "معتمد / Confirmed" and flt(other) + flt(self.amount) > flt(invoice.grand_total):
            frappe.throw("إجمالي التحصيل يتجاوز قيمة الفاتورة / Payments exceed invoice total")

    def on_update(self):
        from wafd_one.finance import refresh_invoice_and_project
        refresh_invoice_and_project(self.invoice)

    def on_trash(self):
        invoice = self.invoice
        frappe.enqueue("wafd_one.finance.refresh_invoice_and_project", invoice_name=invoice, enqueue_after_commit=True)
