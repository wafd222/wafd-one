import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate

class WafdInvoice(Document):
    def validate(self):
        if not self.invoice_date:
            self.invoice_date = nowdate()
        if self.due_date and getdate(self.due_date) < getdate(self.invoice_date):
            frappe.throw("تاريخ الاستحقاق لا يمكن أن يسبق تاريخ الفاتورة / Due date cannot precede invoice date")
        if self.billing_basis == "قيمة العقد / Contract Value":
            self.subtotal = flt(frappe.db.get_value("WAFD Catering Project", self.project, "contract_value"))
        elif self.billing_basis == "الكميات المسلمة / Delivered Quantities":
            self.subtotal = sum(flt(row.amount) for row in (self.items or []))
        self.tax_amount = flt(self.subtotal) * flt(self.tax_rate) / 100
        self.grand_total = flt(self.subtotal) + flt(self.tax_amount)
        confirmed = 0
        if not self.is_new():
            confirmed = frappe.db.sql("""select coalesce(sum(amount),0) from `tabWAFD Payment` where invoice=%s and status='معتمد / Confirmed'""", self.name)[0][0]
        self.paid_amount = flt(confirmed)
        self.balance = max(flt(self.grand_total) - flt(self.paid_amount), 0)
        if self.status != "ملغاة / Cancelled":
            if self.balance <= 0 and self.grand_total > 0:
                self.status = "مدفوعة / Paid"
            elif self.paid_amount > 0:
                self.status = "مدفوعة جزئياً / Partially Paid"
            elif self.due_date and getdate(self.due_date) < getdate(nowdate()):
                self.status = "متأخرة / Overdue"

    def on_update(self):
        from wafd_one.finance import refresh_project_financials
        refresh_project_financials(self.project)
