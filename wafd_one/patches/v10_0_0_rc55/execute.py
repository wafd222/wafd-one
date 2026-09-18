import frappe
from frappe.utils import flt, getdate, nowdate


def execute():
    if not frappe.db.exists("DocType", "WAFD Invoice"):
        return

    # Ensure metadata reflects the production-safe finance workflow immediately.
    frappe.reload_doc("wafd_one", "doctype", "wafd_invoice")

    invoices = frappe.get_all(
        "WAFD Invoice",
        fields=["name", "grand_total", "due_date", "status"],
    )
    for row in invoices:
        if row.status == "ملغاة / Cancelled":
            continue
        paid = flt(
            frappe.db.sql(
                """select coalesce(sum(amount), 0) from `tabWAFD Payment`
                   where invoice=%s and status='معتمد / Confirmed'""",
                row.name,
            )[0][0],
            2,
        )
        total = flt(row.grand_total, 2)
        balance = max(flt(total - paid, 2), 0)
        if total <= 0:
            status = "مسودة / Draft"
        elif balance <= 0:
            status = "مدفوعة / Paid"
        elif paid > 0:
            status = "مدفوعة جزئياً / Partially Paid"
        elif row.due_date and getdate(row.due_date) < getdate(nowdate()):
            status = "متأخرة / Overdue"
        else:
            status = "غير مدفوعة / Unpaid"
        frappe.db.set_value(
            "WAFD Invoice",
            row.name,
            {"paid_amount": paid, "balance": balance, "status": status},
            update_modified=False,
        )
