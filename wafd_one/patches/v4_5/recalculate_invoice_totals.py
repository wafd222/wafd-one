import frappe
from frappe.utils import flt, getdate, nowdate


def execute():
    """Repair totals/status on invoices created before v4.5.0.

    This deliberately uses direct database updates so legacy invoices with incomplete
    delivered-item rows can still be repaired without triggering unrelated validation.
    """
    invoices = frappe.db.get_all(
        "WAFD Invoice",
        fields=["name", "subtotal", "tax_rate", "paid_amount", "due_date", "status"],
    )
    for invoice in invoices:
        subtotal = flt(invoice.subtotal, 2)
        tax_rate = flt(invoice.tax_rate, 2)
        tax_amount = flt(subtotal * tax_rate / 100, 2)
        grand_total = flt(subtotal + tax_amount, 2)
        paid_amount = flt(
            frappe.db.sql(
                """select coalesce(sum(amount), 0) from `tabWAFD Payment`
                   where invoice=%s and status='معتمد / Confirmed'""",
                (invoice.name,),
            )[0][0],
            2,
        )
        balance = max(flt(grand_total - paid_amount, 2), 0)

        status = invoice.status
        if status != "ملغاة / Cancelled":
            if grand_total <= 0:
                status = "مسودة / Draft"
            elif balance <= 0:
                status = "مدفوعة / Paid"
            elif paid_amount > 0:
                status = "مدفوعة جزئياً / Partially Paid"
            elif invoice.due_date and getdate(invoice.due_date) < getdate(nowdate()):
                status = "متأخرة / Overdue"
            elif status not in ("مسودة / Draft", "مرسلة / Sent"):
                status = "مرسلة / Sent"

        frappe.db.set_value(
            "WAFD Invoice",
            invoice.name,
            {
                "tax_amount": tax_amount,
                "grand_total": grand_total,
                "paid_amount": paid_amount,
                "balance": balance,
                "status": status,
            },
            update_modified=False,
        )
