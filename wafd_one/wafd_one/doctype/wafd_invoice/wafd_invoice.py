import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class WAFDInvoice(Document):
    def validate(self):
        if not self.invoice_date:
            self.invoice_date = nowdate()
        if self.due_date and getdate(self.due_date) < getdate(self.invoice_date):
            frappe.throw("تاريخ الاستحقاق لا يمكن أن يسبق تاريخ الفاتورة / Due date cannot precede invoice date")

        if self.billing_basis == "قيمة العقد / Contract Value":
            self.subtotal = flt(frappe.db.get_value("WAFD Catering Project", self.project, "contract_value"))
        elif self.billing_basis == "الكميات المسلمة / Delivered Quantities":
            self._recalculate_delivered_items()
            self.subtotal = sum(flt(row.amount) for row in (self.items or []))

        self.tax_amount = flt(self.subtotal) * flt(self.tax_rate) / 100
        self.grand_total = flt(self.subtotal) + flt(self.tax_amount)

        if self.billing_basis != "يدوي / Manual" and flt(self.grand_total) <= 0:
            frappe.throw(
                "لا يمكن حفظ فاتورة بقيمة صفر. حدد سعر الوحدة في خطة الوجبة أو خدمات المشروع، "
                "أو استخدم الفوترة اليدوية / Zero-value invoices are not allowed. Set a unit price "
                "in the meal plan or project services, or use manual billing."
            )

        confirmed = 0
        if not self.is_new():
            confirmed = frappe.db.sql(
                """select coalesce(sum(amount),0) from `tabWAFD Payment`
                   where invoice=%s and status='معتمد / Confirmed'""",
                self.name,
            )[0][0]
        self.paid_amount = flt(confirmed)
        self.balance = max(flt(self.grand_total) - self.paid_amount, 0)
        self._set_status()

    def _recalculate_delivered_items(self):
        from wafd_one.finance import resolve_unit_price

        if not self.items:
            frappe.throw("لا توجد بنود فاتورة / Invoice has no items")
        missing = []
        for row in self.items:
            row.delivered_quantity = flt(row.delivered_quantity)
            if row.delivered_quantity <= 0:
                frappe.throw("كمية البند يجب أن تكون أكبر من صفر / Invoice item quantity must be greater than zero")
            row.unit_price = flt(row.unit_price) or resolve_unit_price(
                self.project, row.meal_plan, row.meal_type
            )
            if row.unit_price <= 0:
                missing.append(row.meal_plan or str(row.idx))
            row.amount = row.delivered_quantity * row.unit_price
        if missing:
            frappe.throw(
                "تعذر تحديد سعر الوحدة للبنود: {0} / Unable to resolve unit price for items: {0}".format(
                    ", ".join(missing)
                )
            )

    def _set_status(self):
        if self.status == "ملغاة / Cancelled":
            return
        if flt(self.grand_total) <= 0:
            self.status = "مسودة / Draft"
        elif self.balance <= 0:
            self.status = "مدفوعة / Paid"
        elif self.paid_amount > 0:
            self.status = "مدفوعة جزئياً / Partially Paid"
        elif self.due_date and getdate(self.due_date) < getdate(nowdate()):
            self.status = "متأخرة / Overdue"
        elif self.status not in ("مسودة / Draft", "مرسلة / Sent"):
            self.status = "مرسلة / Sent"

    def on_update(self):
        from wafd_one.finance import refresh_project_financials
        refresh_project_financials(self.project)
