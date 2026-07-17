import frappe
from frappe.utils import add_days, flt, getdate, nowdate


def _scalar(query, values=None):
    return frappe.db.sql(query, values or ())[0][0]


def refresh_invoice_and_project(invoice_name):
    if not invoice_name or not frappe.db.exists("WAFD Invoice", invoice_name):
        return

    invoice = frappe.get_doc("WAFD Invoice", invoice_name)
    paid = _scalar(
        """select coalesce(sum(amount), 0)
           from `tabWAFD Payment`
           where invoice=%s and status='معتمد / Confirmed'""",
        (invoice_name,),
    )
    balance = max(flt(invoice.grand_total) - flt(paid), 0)
    status = invoice.status
    if status != "ملغاة / Cancelled":
        if balance <= 0 and flt(invoice.grand_total) > 0:
            status = "مدفوعة / Paid"
        elif flt(paid) > 0:
            status = "مدفوعة جزئياً / Partially Paid"
        elif invoice.due_date and getdate(invoice.due_date) < getdate(nowdate()):
            status = "متأخرة / Overdue"

    frappe.db.set_value(
        "WAFD Invoice",
        invoice_name,
        {"paid_amount": paid, "balance": balance, "status": status},
        update_modified=False,
    )
    refresh_project_financials(invoice.project)


@frappe.whitelist()
def refresh_project_financials(project_name):
    if not project_name or not frappe.db.exists("WAFD Catering Project", project_name):
        return

    costs = _scalar(
        """select coalesce(sum(amount), 0)
           from `tabWAFD Project Cost`
           where project=%s and status not in ('ملغي / Cancelled', 'مسودة / Draft')""",
        (project_name,),
    )
    revenues = _scalar(
        """select coalesce(sum(amount), 0)
           from `tabWAFD Project Revenue`
           where project=%s and status='محصل / Collected'""",
        (project_name,),
    )
    invoice_paid = _scalar(
        """select coalesce(sum(p.amount), 0)
           from `tabWAFD Payment` p
           inner join `tabWAFD Invoice` i on i.name=p.invoice
           where p.project=%s and p.status='معتمد / Confirmed'
             and i.status!='ملغاة / Cancelled'""",
        (project_name,),
    )
    revenue = max(flt(revenues), flt(invoice_paid))
    delivered = _scalar(
        """select coalesce(sum(received_quantity), 0)
           from `tabWAFD Delivery Proof`
           where project=%s and status in
             ('مقبول بالكامل / Fully Accepted', 'مقبول جزئياً / Partially Accepted')""",
        (project_name,),
    )
    total = flt(frappe.db.get_value("WAFD Catering Project", project_name, "total_meals"))
    profit = revenue - flt(costs)
    frappe.db.set_value(
        "WAFD Catering Project",
        project_name,
        {
            "actual_cost": costs,
            "revenue": revenue,
            "profit": profit,
            "profit_margin_percent": profit / revenue * 100 if revenue else 0,
            "delivered_meals": delivered,
            "remaining_meals": max(total - flt(delivered), 0),
            "progress_percent": flt(delivered) / total * 100 if total else 0,
        },
        update_modified=False,
    )


@frappe.whitelist()
def create_invoice_from_deliveries(project_name, tax_rate=15, due_date=None):
    project = frappe.get_doc("WAFD Catering Project", project_name)
    project.check_permission("write")
    plans = frappe.db.sql(
        """select mp.name, mp.service_date, mp.hotel, mp.meal_type, mp.unit_price,
                  coalesce(sum(dp.received_quantity), 0) delivered_quantity
           from `tabWAFD Meal Plan` mp
           left join `tabWAFD Delivery Proof` dp
             on dp.meal_plan=mp.name
            and dp.status in ('مقبول بالكامل / Fully Accepted', 'مقبول جزئياً / Partially Accepted')
           where mp.project=%s
           group by mp.name, mp.service_date, mp.hotel, mp.meal_type, mp.unit_price
           having delivered_quantity > 0""",
        (project_name,),
        as_dict=True,
    )
    if not plans:
        frappe.throw("لا توجد كميات مسلمة قابلة للفوترة / No delivered quantities to invoice")

    already = set(
        frappe.db.sql_list(
            """select distinct ii.meal_plan
               from `tabWAFD Invoice Item` ii
               inner join `tabWAFD Invoice` i on i.name=ii.parent
               where ii.parenttype='WAFD Invoice'
                 and i.status!='ملغاة / Cancelled'
                 and ifnull(ii.meal_plan, '')!=''"""
        )
    )
    rows = [p for p in plans if p.name not in already]
    if not rows:
        frappe.throw("تمت فوترة جميع الكميات المسلمة / All delivered quantities are already invoiced")

    inv = frappe.get_doc(
        {
            "doctype": "WAFD Invoice",
            "project": project_name,
            "invoice_date": nowdate(),
            "due_date": due_date,
            "billing_basis": "الكميات المسلمة / Delivered Quantities",
            "tax_rate": flt(tax_rate),
            "status": "مسودة / Draft",
            "description": "فاتورة مبنية على الكميات المسلمة / Invoice based on delivered quantities",
        }
    )
    for row in rows:
        inv.append(
            "items",
            {
                "meal_plan": row.name,
                "service_date": row.service_date,
                "hotel": row.hotel,
                "meal_type": row.meal_type,
                "delivered_quantity": row.delivered_quantity,
                "unit_price": row.unit_price,
                "amount": flt(row.delivered_quantity) * flt(row.unit_price),
            },
        )
    inv.insert()
    return inv.name


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None):
    """Return executive KPIs and exception lists for the WAFD ONE dashboard."""
    to_date = getdate(to_date or nowdate())
    from_date = getdate(from_date or add_days(to_date, -6))
    if from_date > to_date:
        frappe.throw("تاريخ البداية يجب أن يسبق تاريخ النهاية / From date must be before to date")

    date_values = (from_date, to_date)
    active = frappe.db.count(
        "WAFD Catering Project", {"status": ["in", ["تخطيط / Planning", "نشط / Active"]]}
    )
    planned = _scalar(
        """select coalesce(sum(quantity), 0) from `tabWAFD Meal Plan`
           where service_date between %s and %s and status!='ملغي / Cancelled'""",
        date_values,
    )
    produced = _scalar(
        """select coalesce(sum(produced_quantity), 0) from `tabWAFD Production Batch`
           where batch_date between %s and %s and status!='موقوف / Stopped'""",
        date_values,
    )
    delivered = _scalar(
        """select coalesce(sum(received_quantity), 0) from `tabWAFD Delivery Proof`
           where date(delivery_time) between %s and %s
             and status in ('مقبول بالكامل / Fully Accepted', 'مقبول جزئياً / Partially Accepted')""",
        date_values,
    )
    rejected = _scalar(
        """select coalesce(sum(rejected_quantity), 0) from `tabWAFD Delivery Proof`
           where date(delivery_time) between %s and %s""",
        date_values,
    )
    receivable = _scalar(
        """select coalesce(sum(balance), 0) from `tabWAFD Invoice`
           where status not in ('مدفوعة / Paid', 'ملغاة / Cancelled')"""
    )
    overdue = _scalar(
        """select coalesce(sum(balance), 0) from `tabWAFD Invoice`
           where due_date < %s and balance > 0 and status!='ملغاة / Cancelled'""",
        (nowdate(),),
    )
    costs = _scalar(
        """select coalesce(sum(amount), 0) from `tabWAFD Project Cost`
           where cost_date between %s and %s
             and status not in ('ملغي / Cancelled', 'مسودة / Draft')""",
        date_values,
    )
    revenue = _scalar(
        """select coalesce(sum(amount), 0) from `tabWAFD Payment`
           where payment_date between %s and %s and status='معتمد / Confirmed'""",
        date_values,
    )

    alerts = {
        "material_shortages": frappe.db.count("WAFD Production Batch", {"materials_status": "عجز / Shortage"}),
        "quality_rejected": frappe.db.count("WAFD Production Batch", {"quality_status": "مرفوض / Rejected"}),
        "late_trips": frappe.db.count(
            "WAFD Delivery Trip",
            {"planned_arrival": ["<", frappe.utils.now()], "status": ["in", ["مخططة / Planned", "تم التحميل / Loaded", "في الطريق / In Transit"]]},
        ),
        "overdue_invoices": frappe.db.count(
            "WAFD Invoice",
            {"due_date": ["<", nowdate()], "balance": [">", 0], "status": ["!=", "ملغاة / Cancelled"]},
        ),
    }

    active_projects = frappe.db.get_all(
        "WAFD Catering Project",
        filters={"status": ["in", ["تخطيط / Planning", "نشط / Active"]]},
        fields=["name", "project_name", "status", "progress_percent", "total_meals", "delivered_meals", "profit"],
        order_by="end_date asc",
        limit=8,
    )
    upcoming_deliveries = frappe.db.get_all(
        "WAFD Delivery Trip",
        filters={"trip_date": ["between", [nowdate(), add_days(nowdate(), 2)]], "status": ["not in", ["تم التسليم / Delivered", "ملغية / Cancelled"]]},
        fields=["name", "trip_date", "hotel", "driver", "quantity", "status", "planned_arrival"],
        order_by="trip_date asc, planned_arrival asc",
        limit=10,
    )
    overdue_invoices = frappe.db.get_all(
        "WAFD Invoice",
        filters={"due_date": ["<", nowdate()], "balance": [">", 0], "status": ["!=", "ملغاة / Cancelled"]},
        fields=["name", "project", "due_date", "grand_total", "paid_amount", "balance", "status"],
        order_by="due_date asc",
        limit=10,
    )

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "active_projects": active,
        "planned_meals": planned,
        "produced_meals": produced,
        "delivered_meals": delivered,
        "rejected_meals": rejected,
        "delivery_rate": flt(delivered) / flt(planned) * 100 if planned else 0,
        "receivables": receivable,
        "overdue_receivables": overdue,
        "actual_cost": costs,
        "collected_revenue": revenue,
        "profit": flt(revenue) - flt(costs),
        "alerts": alerts,
        "projects": active_projects,
        "upcoming_deliveries": upcoming_deliveries,
        "overdue_invoices": overdue_invoices,
    }
