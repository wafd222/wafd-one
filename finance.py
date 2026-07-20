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

    project = frappe.db.get_value(
        "WAFD Catering Project", project_name,
        ["estimated_cost", "estimated_revenue", "contract_value", "total_meals"],
        as_dict=True,
    ) or {}
    costs = flt(_scalar(
        """select coalesce(sum(amount), 0) from `tabWAFD Project Cost`
           where project=%s and status in ('معتمد / Approved', 'مدفوع / Paid')""",
        (project_name,),
    ))
    collected_revenue = flt(_scalar(
        """select coalesce(sum(amount), 0) from `tabWAFD Project Revenue`
           where project=%s and status='محصل / Collected'""",
        (project_name,),
    ))
    invoice_paid = flt(_scalar(
        """select coalesce(sum(p.amount), 0) from `tabWAFD Payment` p
           inner join `tabWAFD Invoice` i on i.name=p.invoice
           where p.project=%s and p.status='معتمد / Confirmed'
             and i.status!='ملغاة / Cancelled'""",
        (project_name,),
    ))
    invoiced = flt(_scalar(
        """select coalesce(sum(grand_total), 0) from `tabWAFD Invoice`
           where project=%s and status!='ملغاة / Cancelled'""",
        (project_name,),
    ))
    outstanding = flt(_scalar(
        """select coalesce(sum(balance), 0) from `tabWAFD Invoice`
           where project=%s and status!='ملغاة / Cancelled'""",
        (project_name,),
    ))
    revenue = max(collected_revenue, invoice_paid)
    delivered = flt(_scalar(
        """select coalesce(sum(received_quantity), 0) from `tabWAFD Delivery Proof`
           where project=%s and status in
             ('مقبول بالكامل / Fully Accepted', 'مقبول جزئياً / Partially Accepted')""",
        (project_name,),
    ))
    total = flt(project.get("total_meals"))
    basis_meals = delivered or total
    estimated_revenue = flt(project.get("estimated_revenue")) or flt(project.get("contract_value"))
    estimated_cost = flt(project.get("estimated_cost"))
    profit = revenue - costs
    values = {
        "actual_cost": costs,
        "revenue": revenue,
        "profit": profit,
        "profit_margin_percent": profit / revenue * 100 if revenue else 0,
        "invoiced_amount": invoiced,
        "outstanding_amount": outstanding,
        "cost_variance": costs - estimated_cost,
        "revenue_variance": revenue - estimated_revenue,
        "cost_per_meal": costs / basis_meals if basis_meals else 0,
        "revenue_per_meal": revenue / basis_meals if basis_meals else 0,
        "profit_per_meal": profit / basis_meals if basis_meals else 0,
        "delivered_meals": delivered,
        "remaining_meals": max(total - delivered, 0),
        "progress_percent": delivered / total * 100 if total else 0,
    }
    frappe.db.set_value("WAFD Catering Project", project_name, values, update_modified=False)
    return values


@frappe.whitelist()
def get_financial_intelligence(project_name=None, as_of_date=None):
    """Return project profitability and receivables ageing from posted WAFD records."""
    as_of_date = getdate(as_of_date or nowdate())
    filters = {"status": ["!=", "ملغي / Cancelled"]}
    if project_name:
        filters["name"] = project_name
    projects = frappe.db.get_all(
        "WAFD Catering Project", filters=filters,
        fields=["name", "project_name", "contract_value", "estimated_cost", "estimated_revenue",
                "actual_cost", "revenue", "profit", "profit_margin_percent", "invoiced_amount",
                "outstanding_amount", "delivered_meals", "cost_per_meal", "revenue_per_meal",
                "profit_per_meal", "cost_variance", "revenue_variance"],
        order_by="profit desc",
    )
    for row in projects:
        refresh_project_financials(row.name)
    projects = frappe.db.get_all(
        "WAFD Catering Project", filters=filters,
        fields=["name", "project_name", "contract_value", "estimated_cost", "estimated_revenue",
                "actual_cost", "revenue", "profit", "profit_margin_percent", "invoiced_amount",
                "outstanding_amount", "delivered_meals", "cost_per_meal", "revenue_per_meal",
                "profit_per_meal", "cost_variance", "revenue_variance"],
        order_by="profit desc",
    )
    ageing = {"current": 0.0, "days_1_30": 0.0, "days_31_60": 0.0, "days_61_90": 0.0, "over_90": 0.0}
    invoice_filters = ["status!='ملغاة / Cancelled'", "balance>0"]
    values = []
    if project_name:
        invoice_filters.append("project=%s")
        values.append(project_name)
    invoices = frappe.db.sql(
        f"select name, project, due_date, balance from `tabWAFD Invoice` where {' and '.join(invoice_filters)}",
        tuple(values), as_dict=True,
    )
    for inv in invoices:
        if not inv.due_date or getdate(inv.due_date) >= as_of_date:
            ageing["current"] += flt(inv.balance)
            continue
        days = (as_of_date - getdate(inv.due_date)).days
        key = "days_1_30" if days <= 30 else "days_31_60" if days <= 60 else "days_61_90" if days <= 90 else "over_90"
        ageing[key] += flt(inv.balance)
    totals = {
        "contract_value": sum(flt(x.contract_value) for x in projects),
        "actual_cost": sum(flt(x.actual_cost) for x in projects),
        "collected_revenue": sum(flt(x.revenue) for x in projects),
        "invoiced_amount": sum(flt(x.invoiced_amount) for x in projects),
        "outstanding_amount": sum(flt(x.outstanding_amount) for x in projects),
        "profit": sum(flt(x.profit) for x in projects),
    }
    totals["profit_margin_percent"] = totals["profit"] / totals["collected_revenue"] * 100 if totals["collected_revenue"] else 0
    return {"as_of_date": str(as_of_date), "totals": totals, "ageing": ageing, "projects": projects}


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
    """Return executive KPIs and exception lists for the WAFD ONE dashboard.

    Operational documents can legitimately have an empty business date during old
    test cycles. In that case the document creation date is used, so existing data
    does not disappear from the dashboard. Cancelled records are always excluded.
    """
    to_date = getdate(to_date or nowdate())
    from_date = getdate(from_date or add_days(to_date, -29))
    if from_date > to_date:
        frappe.throw("تاريخ البداية يجب أن يسبق تاريخ النهاية / From date must be before to date")

    date_values = (from_date, to_date)

    # The headline project count represents every usable project in the system.
    # Completed projects remain visible because they still own deliveries, invoices,
    # costs and payments. Cancelled projects alone are excluded.
    projects_count = frappe.db.count(
        "WAFD Catering Project", {"status": ["!=", "ملغي / Cancelled"]}
    )

    planned = _scalar(
        """select coalesce(sum(quantity), 0) from `tabWAFD Meal Plan`
           where coalesce(service_date, date(creation)) between %s and %s
             and status!='ملغي / Cancelled'""",
        date_values,
    )
    produced = _scalar(
        """select coalesce(sum(produced_quantity), 0) from `tabWAFD Production Batch`
           where coalesce(batch_date, date(creation)) between %s and %s
             and status!='موقوف / Stopped'""",
        date_values,
    )
    delivered = _scalar(
        """select coalesce(sum(coalesce(nullif(received_quantity, 0), delivered_quantity, 0)), 0)
           from `tabWAFD Delivery Proof`
           where coalesce(date(delivery_time), date(creation)) between %s and %s
             and status in ('مقبول بالكامل / Fully Accepted', 'مقبول جزئياً / Partially Accepted')""",
        date_values,
    )
    rejected = _scalar(
        """select coalesce(sum(rejected_quantity), 0) from `tabWAFD Delivery Proof`
           where coalesce(date(delivery_time), date(creation)) between %s and %s""",
        date_values,
    )
    invoiced = _scalar(
        """select coalesce(sum(grand_total), 0) from `tabWAFD Invoice`
           where coalesce(invoice_date, date(creation)) between %s and %s
             and status!='ملغاة / Cancelled'""",
        date_values,
    )
    receivable = _scalar(
        """select coalesce(sum(balance), 0) from `tabWAFD Invoice`
           where balance > 0 and status not in ('مدفوعة / Paid', 'ملغاة / Cancelled')"""
    )
    overdue = _scalar(
        """select coalesce(sum(balance), 0) from `tabWAFD Invoice`
           where due_date < %s and balance > 0 and status!='ملغاة / Cancelled'""",
        (nowdate(),),
    )
    costs = _scalar(
        """select coalesce(sum(amount), 0) from `tabWAFD Project Cost`
           where coalesce(cost_date, date(creation)) between %s and %s
             and status not in ('ملغي / Cancelled', 'مسودة / Draft')""",
        date_values,
    )
    revenue = _scalar(
        """select coalesce(sum(amount), 0) from `tabWAFD Payment`
           where coalesce(payment_date, date(creation)) between %s and %s
             and status='معتمد / Confirmed'""",
        date_values,
    )

    # Alerts follow the date selected on the dashboard. This avoids showing KPIs
    # for one period while evaluating exceptions against a different (today-only)
    # period. Old records with an empty operational date fall back to creation.
    alert_reference_date = to_date
    alert_cutoff = f"{alert_reference_date} 23:59:59"

    material_shortages = _scalar(
        """select count(*) from `tabWAFD Production Batch`
           where coalesce(batch_date, date(creation)) between %s and %s
             and materials_status='عجز / Shortage'
             and status!='موقوف / Stopped'""",
        date_values,
    )
    quality_rejected = _scalar(
        """select count(*) from `tabWAFD Production Batch`
           where coalesce(batch_date, date(creation)) between %s and %s
             and quality_status='مرفوض / Rejected'
             and status!='موقوف / Stopped'""",
        date_values,
    )
    late_trips = _scalar(
        """select count(*) from `tabWAFD Delivery Trip`
           where status not in ('تم التسليم / Delivered', 'ملغية / Cancelled')
             and (
                 status='متأخرة / Delayed'
                 or (planned_arrival is not null and planned_arrival < %s)
                 or (planned_arrival is null and coalesce(trip_date, date(creation)) < %s)
             )""",
        (alert_cutoff, alert_reference_date),
    )
    overdue_invoice_count = _scalar(
        """select count(*) from `tabWAFD Invoice`
           where due_date is not null and due_date < %s
             and balance > 0
             and status!='ملغاة / Cancelled'""",
        (alert_reference_date,),
    )
    unpaid_invoice_count = _scalar(
        """select count(*) from `tabWAFD Invoice`
           where balance > 0
             and status not in ('مدفوعة / Paid', 'ملغاة / Cancelled')"""
    )

    alerts = {
        "material_shortages": int(material_shortages or 0),
        "quality_rejected": int(quality_rejected or 0),
        "late_trips": int(late_trips or 0),
        "overdue_invoices": int(overdue_invoice_count or 0),
        "unpaid_invoices": int(unpaid_invoice_count or 0),
        "production_gap": max(flt(planned) - flt(produced), 0),
        "delivery_without_production": max(flt(delivered) - flt(produced), 0),
    }

    projects = frappe.db.get_all(
        "WAFD Catering Project",
        filters={"status": ["!=", "ملغي / Cancelled"]},
        fields=[
            "name",
            "project_name",
            "status",
            "progress_percent",
            "total_meals",
            "delivered_meals",
            "profit",
        ],
        order_by="modified desc",
        limit=8,
    )
    upcoming_deliveries = frappe.db.get_all(
        "WAFD Delivery Trip",
        filters={
            "trip_date": ["between", [nowdate(), add_days(nowdate(), 2)]],
            "status": ["not in", ["تم التسليم / Delivered", "ملغية / Cancelled"]],
        },
        fields=["name", "trip_date", "hotel", "driver", "quantity", "status", "planned_arrival"],
        order_by="trip_date asc, planned_arrival asc",
        limit=10,
    )
    overdue_invoices = frappe.db.get_all(
        "WAFD Invoice",
        filters={
            "due_date": ["<", alert_reference_date],
            "balance": [">", 0],
            "status": ["!=", "ملغاة / Cancelled"],
        },
        fields=["name", "project", "due_date", "grand_total", "paid_amount", "balance", "status"],
        order_by="due_date asc",
        limit=10,
    )

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "active_projects": projects_count,
        "planned_meals": flt(planned),
        "produced_meals": flt(produced),
        "delivered_meals": flt(delivered),
        "rejected_meals": flt(rejected),
        "delivery_rate": flt(delivered) / flt(planned) * 100 if planned else 0,
        "invoiced_revenue": flt(invoiced),
        "receivables": flt(receivable),
        "overdue_receivables": flt(overdue),
        "actual_cost": flt(costs),
        "collected_revenue": flt(revenue),
        "profit": flt(revenue) - flt(costs),
        "alerts": alerts,
        "projects": projects,
        "upcoming_deliveries": upcoming_deliveries,
        "overdue_invoices": overdue_invoices,
    }
