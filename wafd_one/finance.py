import frappe
from frappe.utils import add_days, flt, getdate, nowdate


def _scalar(query, values=None):
    return frappe.db.sql(query, values or ())[0][0]


def _confirmed_payments(invoice_name, exclude_payment=None):
    conditions = ["invoice=%s", "status='معتمد / Confirmed'"]
    values = [invoice_name]
    if exclude_payment:
        conditions.append("name!=%s")
        values.append(exclude_payment)
    return flt(
        _scalar(
            f"select coalesce(sum(amount), 0) from `tabWAFD Payment` where {' and '.join(conditions)}",
            tuple(values),
        )
    )


def resolve_unit_price(project_name, meal_plan_name=None, meal_type=None):
    """Resolve a billable unit price using explicit and auditable fallbacks."""
    if meal_plan_name:
        price = flt(frappe.db.get_value("WAFD Meal Plan", meal_plan_name, "unit_price"))
        if price > 0:
            return price

    if project_name:
        services = frappe.db.get_all(
            "WAFD Project Service",
            filters={"parent": project_name, "parenttype": "WAFD Catering Project"},
            fields=["service_type", "unit_price"],
            order_by="idx asc",
        )
        for service in services:
            if flt(service.unit_price) > 0 and (not meal_type or service.service_type == meal_type):
                return flt(service.unit_price)
        for service in services:
            if flt(service.unit_price) > 0:
                return flt(service.unit_price)

        values = frappe.db.get_value(
            "WAFD Catering Project", project_name, ["contract_value", "total_meals"], as_dict=True
        ) or {}
        if flt(values.get("contract_value")) > 0 and flt(values.get("total_meals")) > 0:
            return flt(values.contract_value) / flt(values.total_meals)

    return 0


@frappe.whitelist()
def get_invoice_totals(invoice_name, exclude_payment=None):
    invoice = frappe.db.get_value(
        "WAFD Invoice", invoice_name, ["project", "grand_total", "status"], as_dict=True
    )
    if not invoice:
        frappe.throw("الفاتورة غير موجودة / Invoice not found")
    paid = _confirmed_payments(invoice_name, exclude_payment=exclude_payment)
    total = flt(invoice.grand_total)
    return {
        "project": invoice.project,
        "invoice_total": total,
        "paid_amount": paid,
        "balance": max(total - paid, 0),
        "status": invoice.status,
    }


def refresh_invoice_and_project(invoice_name):
    if not invoice_name or not frappe.db.exists("WAFD Invoice", invoice_name):
        return

    invoice = frappe.get_doc("WAFD Invoice", invoice_name)
    paid = _confirmed_payments(invoice_name)
    total = flt(invoice.grand_total)
    balance = max(total - paid, 0)
    status = invoice.status
    if status != "ملغاة / Cancelled":
        if total <= 0:
            status = "مسودة / Draft"
        elif balance <= 0:
            status = "مدفوعة / Paid"
        elif paid > 0:
            status = "مدفوعة جزئياً / Partially Paid"
        elif invoice.due_date and getdate(invoice.due_date) < getdate(nowdate()):
            status = "متأخرة / Overdue"
        elif status not in ("مسودة / Draft", "مرسلة / Sent"):
            status = "مرسلة / Sent"

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
    rows = _get_billable_delivery_rows(project_name)
    if not rows:
        frappe.throw("لا توجد كميات مسلمة قابلة للفوترة / No delivered quantities to invoice")

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
    _append_delivery_rows(inv, rows)
    inv.insert()
    return inv.name


def _get_billable_delivery_rows(project_name, exclude_invoice=None):
    """Return only the accepted delivered quantity that is still available to invoice.

    Quantities are calculated per meal plan as accepted delivery proofs minus quantities
    already reserved by non-cancelled invoices. This allows later incremental deliveries
    for the same meal plan to be invoiced without duplicating earlier quantities.
    """
    plans = frappe.db.sql(
        """select mp.name, mp.service_date, mp.hotel, mp.meal_type, mp.unit_price,
                  coalesce(sum(dp.received_quantity), 0) delivered_quantity
           from `tabWAFD Meal Plan` mp
           inner join `tabWAFD Delivery Proof` dp
             on dp.meal_plan=mp.name
            and dp.project=mp.project
            and dp.status in ('مقبول بالكامل / Fully Accepted', 'مقبول جزئياً / Partially Accepted')
           where mp.project=%s
           group by mp.name, mp.service_date, mp.hotel, mp.meal_type, mp.unit_price
           having delivered_quantity > 0""",
        (project_name,),
        as_dict=True,
    )

    conditions = [
        "ii.parenttype='WAFD Invoice'",
        "ii.parentfield='items'",
        "i.project=%s",
        "i.status!='ملغاة / Cancelled'",
        "ifnull(ii.meal_plan, '')!=''",
    ]
    values = [project_name]
    if exclude_invoice:
        conditions.append("i.name!=%s")
        values.append(exclude_invoice)

    invoiced_rows = frappe.db.sql(
        f"""select ii.meal_plan, coalesce(sum(ii.delivered_quantity), 0) invoiced_quantity
            from `tabWAFD Invoice Item` ii
            inner join `tabWAFD Invoice` i on i.name=ii.parent
            where {' and '.join(conditions)}
            group by ii.meal_plan""",
        tuple(values),
        as_dict=True,
    )
    invoiced_by_plan = {row.meal_plan: flt(row.invoiced_quantity) for row in invoiced_rows}

    billable = []
    for row in plans:
        remaining = max(flt(row.delivered_quantity) - invoiced_by_plan.get(row.name, 0), 0)
        if remaining <= 0:
            continue
        row.delivered_quantity = remaining
        billable.append(row)
    return billable


@frappe.whitelist()
def get_uninvoiced_delivery_items(project_name, invoice_name=None):
    """Return accepted delivery quantities that can be loaded into an invoice form."""
    if not project_name:
        return []
    if not frappe.has_permission("WAFD Catering Project", "read", project_name):
        frappe.throw("غير مصرح لك بعرض هذا المشروع / You are not permitted to view this project")

    rows = _get_billable_delivery_rows(project_name, exclude_invoice=invoice_name)
    result = []
    for row in rows:
        unit_price = flt(row.unit_price) or resolve_unit_price(project_name, row.name, row.meal_type)
        result.append({
            "meal_plan": row.name,
            "service_date": row.service_date,
            "hotel": row.hotel,
            "meal_type": row.meal_type,
            "delivered_quantity": flt(row.delivered_quantity),
            "unit_price": unit_price,
            "amount": flt(row.delivered_quantity) * unit_price,
        })
    return result


def _append_delivery_rows(invoice, rows):
    missing_prices = []
    for row in rows:
        unit_price = flt(row.unit_price) or resolve_unit_price(
            invoice.project, row.name, row.meal_type
        )
        if unit_price <= 0:
            missing_prices.append(row.name)
        invoice.append(
            "items",
            {
                "meal_plan": row.name,
                "service_date": row.service_date,
                "hotel": row.hotel,
                "meal_type": row.meal_type,
                "delivered_quantity": flt(row.delivered_quantity),
                "unit_price": unit_price,
                "amount": flt(row.delivered_quantity) * unit_price,
            },
        )
    if missing_prices:
        frappe.throw(
            "يرجى تحديد سعر الوحدة في خطة الوجبة أو خدمات المشروع قبل إنشاء الفاتورة: {0} / "
            "Set a unit price in the meal plan or project services before invoicing: {0}".format(
                ", ".join(missing_prices)
            )
        )


@frappe.whitelist()
def rebuild_invoice(invoice_name):
    """Rebuild a legacy or zero-value invoice from accepted delivery proofs."""
    invoice = frappe.get_doc("WAFD Invoice", invoice_name)
    invoice.check_permission("write")
    if invoice.status == "ملغاة / Cancelled":
        frappe.throw("لا يمكن إعادة احتساب فاتورة ملغاة / Cannot rebuild a cancelled invoice")
    if _confirmed_payments(invoice.name) > 0:
        frappe.throw(
            "لا يمكن إعادة بناء فاتورة عليها تحصيلات معتمدة / "
            "Cannot rebuild an invoice with confirmed payments"
        )

    rows = _get_billable_delivery_rows(invoice.project, exclude_invoice=invoice.name)
    if not rows:
        frappe.throw(
            "لا توجد كميات مسلمة غير مفوترة لإعادة بناء الفاتورة / "
            "No uninvoiced delivered quantities are available to rebuild this invoice"
        )

    invoice.set("items", [])
    invoice.billing_basis = "الكميات المسلمة / Delivered Quantities"
    _append_delivery_rows(invoice, rows)
    invoice.save()
    return invoice.name


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
    invoiced = _scalar(
        """select coalesce(sum(grand_total), 0) from `tabWAFD Invoice`
           where invoice_date between %s and %s and status!='ملغاة / Cancelled'""",
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
        "invoiced_revenue": invoiced,
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
