import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class WAFDPayment(Document):
    def validate(self):
        if not self.payment_date:
            self.payment_date = nowdate()
        if not self.invoice:
            frappe.throw("الفاتورة مطلوبة / Invoice is required")

        from wafd_one.finance import get_invoice_totals, get_finance_settings

        totals = get_invoice_totals(
            self.invoice,
            exclude_payment=self.name if not self.is_new() else None,
        )
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
        if flt(self.outstanding_before) <= 0:
            frappe.throw("الفاتورة مدفوعة بالكامل ولا يمكن إنشاء تحصيل إضافي / Invoice is fully paid; another payment cannot be created")
        if flt(self.amount) <= 0:
            frappe.throw("مبلغ التحصيل يجب أن يكون أكبر من صفر / Payment must be greater than zero")
        if flt(self.amount) > flt(self.outstanding_before):
            frappe.throw(
                "مبلغ التحصيل يتجاوز الرصيد المتبقي ({0}) / Payment exceeds outstanding balance ({0})".format(
                    frappe.format_value(self.outstanding_before, {"fieldtype": "Currency"})
                )
            )

        settings = get_finance_settings()
        if (
            self.payment_method != "نقدي / Cash"
            and settings.get("require_reference_for_non_cash")
            and not self.reference_number
        ):
            frappe.throw(
                "رقم المرجع مطلوب للتحصيل غير النقدي / Reference number is required for non-cash payments"
            )
        if self.reference_number:
            duplicate = frappe.db.exists(
                "WAFD Payment",
                {
                    "name": ["!=", self.name or ""],
                    "reference_number": self.reference_number,
                    "payment_method": self.payment_method,
                    "docstatus": 1,
                },
            )
            if duplicate:
                frappe.throw(
                    "رقم المرجع مستخدم في تحصيل معتمد آخر / Reference number is already used by another submitted payment"
                )

    def before_submit(self):
        from wafd_one.governance import approval_required, ensure_approved

        if approval_required(self):
            ensure_approved(self, "اعتماد التحصيل / payment submission")

    def on_submit(self):
        self.db_set("status", "معتمد / Confirmed", update_modified=False)
        self._refresh_invoice()

    def on_cancel(self):
        self.db_set("status", "ملغي / Cancelled", update_modified=False)
        self._refresh_invoice()

    def on_update(self):
        # Draft payments never enter the paid total, but refreshing keeps the
        # invoice display consistent after legacy-data migration or edits.
        self._refresh_invoice()

    def on_trash(self):
        if self.docstatus == 1:
            frappe.throw("يجب إلغاء التحصيل قبل حذفه / Cancel the payment before deleting it")
        invoice = self.invoice
        if invoice:
            frappe.enqueue(
                "wafd_one.finance.refresh_invoice_and_project",
                invoice_name=invoice,
                enqueue_after_commit=True,
            )

    def _refresh_invoice(self):
        if not self.invoice:
            return
        from wafd_one.finance import refresh_invoice_and_project

        refresh_invoice_and_project(self.invoice)


@frappe.whitelist()
def submit_and_finish(payment_name):
    """Submit a payment, refresh its invoice, close the project and return the next route.

    This explicit server action avoids relying on a browser on_submit callback and makes
    the final workflow step atomic and repeat-safe.
    """
    if not payment_name or not frappe.db.exists("WAFD Payment", payment_name):
        frappe.throw("سند التحصيل غير موجود / Payment not found")

    payment = frappe.get_doc("WAFD Payment", payment_name)
    payment.check_permission("write")
    if payment.docstatus == 0:
        from wafd_one.finance import get_invoice_totals
        totals = get_invoice_totals(payment.invoice, exclude_payment=payment.name)
        if flt(totals.get("balance")) <= 0:
            invoice = payment.invoice
            project = payment.project or totals.get("project")
            frappe.delete_doc("WAFD Payment", payment.name, ignore_permissions=True, force=True)
            return {
                "already_paid": True,
                "invoice": invoice,
                "project": project,
                "route": ["Form", "WAFD Invoice", invoice],
            }
        payment.submit()
    elif payment.docstatus != 1:
        frappe.throw("لا يمكن اعتماد سند تحصيل ملغي / A cancelled payment cannot be submitted")

    from wafd_one.finance import refresh_invoice_and_project, close_project_financially

    refresh_invoice_and_project(payment.invoice)
    project = payment.project or frappe.db.get_value("WAFD Invoice", payment.invoice, "project")
    closure = None
    if project:
        closure = close_project_financially(project)

    return {
        "payment": payment.name,
        "invoice": payment.invoice,
        "project": project,
        "project_status": frappe.db.get_value("WAFD Catering Project", project, "status") if project else None,
        "closure": closure,
        "route": "wafd-one-dashboard",
    }


@frappe.whitelist()
def discard_paid_invoice_draft(payment_name):
    """Remove a stale draft payment when its invoice is already fully paid."""
    if not payment_name or not frappe.db.exists("WAFD Payment", payment_name):
        return {"deleted": False}
    payment = frappe.get_doc("WAFD Payment", payment_name)
    payment.check_permission("delete")
    if payment.docstatus != 0:
        return {"deleted": False}
    from wafd_one.finance import get_invoice_totals
    totals = get_invoice_totals(payment.invoice, exclude_payment=payment.name)
    if flt(totals.get("balance")) > 0:
        frappe.throw("لا يمكن حذف المسودة لأن الفاتورة ما زالت تحتوي على رصيد / Draft cannot be discarded while the invoice still has a balance")
    invoice = payment.invoice
    frappe.delete_doc("WAFD Payment", payment.name, ignore_permissions=True, force=True)
    return {"deleted": True, "invoice": invoice}
