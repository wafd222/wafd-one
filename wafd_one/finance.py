import frappe
from frappe.utils import flt, nowdate

def refresh_invoice_and_project(invoice_name):
    if not invoice_name or not frappe.db.exists("WAFD Invoice", invoice_name):
        return
    invoice = frappe.get_doc("WAFD Invoice", invoice_name)
    paid = frappe.db.sql("""select coalesce(sum(amount),0) from `tabWAFD Payment` where invoice=%s and status='معتمد / Confirmed'""", invoice_name)[0][0]
    balance = max(flt(invoice.grand_total)-flt(paid),0)
    status = invoice.status
    if status != "ملغاة / Cancelled":
        if balance <= 0 and flt(invoice.grand_total)>0: status="مدفوعة / Paid"
        elif flt(paid)>0: status="مدفوعة جزئياً / Partially Paid"
        elif invoice.due_date and str(invoice.due_date) < nowdate(): status="متأخرة / Overdue"
    frappe.db.set_value("WAFD Invoice", invoice_name, {"paid_amount":paid,"balance":balance,"status":status}, update_modified=False)
    refresh_project_financials(invoice.project)

@frappe.whitelist()
def refresh_project_financials(project_name):
    if not project_name or not frappe.db.exists("WAFD Catering Project", project_name): return
    costs = frappe.db.sql("""select coalesce(sum(amount),0) from `tabWAFD Project Cost` where project=%s and status not in ('ملغي / Cancelled','مسودة / Draft')""", project_name)[0][0]
    revenues = frappe.db.sql("""select coalesce(sum(amount),0) from `tabWAFD Project Revenue` where project=%s and status='محصل / Collected'""", project_name)[0][0]
    invoice_paid = frappe.db.sql("""select coalesce(sum(p.amount),0) from `tabWAFD Payment` p inner join `tabWAFD Invoice` i on i.name=p.invoice where p.project=%s and p.status='معتمد / Confirmed' and i.status!='ملغاة / Cancelled'""", project_name)[0][0]
    revenue = max(flt(revenues), flt(invoice_paid))
    delivered = frappe.db.sql("""select coalesce(sum(received_quantity),0) from `tabWAFD Delivery Proof` where project=%s and status in ('مقبول بالكامل / Fully Accepted','مقبول جزئياً / Partially Accepted')""", project_name)[0][0]
    total = flt(frappe.db.get_value("WAFD Catering Project", project_name, "total_meals"))
    profit = revenue-flt(costs)
    frappe.db.set_value("WAFD Catering Project", project_name, {"actual_cost":costs,"revenue":revenue,"profit":profit,"profit_margin_percent":profit/revenue*100 if revenue else 0,"delivered_meals":delivered,"remaining_meals":max(total-flt(delivered),0),"progress_percent":flt(delivered)/total*100 if total else 0}, update_modified=False)

@frappe.whitelist()
def create_invoice_from_deliveries(project_name, tax_rate=15, due_date=None):
    project=frappe.get_doc("WAFD Catering Project", project_name); project.check_permission("write")
    plans=frappe.db.sql("""select mp.name,mp.service_date,mp.hotel,mp.meal_type,mp.unit_price,coalesce(sum(dp.received_quantity),0) delivered_quantity from `tabWAFD Meal Plan` mp left join `tabWAFD Delivery Proof` dp on dp.meal_plan=mp.name and dp.status in ('مقبول بالكامل / Fully Accepted','مقبول جزئياً / Partially Accepted') where mp.project=%s group by mp.name,mp.service_date,mp.hotel,mp.meal_type,mp.unit_price having delivered_quantity>0""", project_name, as_dict=True)
    if not plans: frappe.throw("لا توجد كميات مسلمة قابلة للفوترة / No delivered quantities to invoice")
    already = set(frappe.db.sql_list("""
        select distinct ii.meal_plan
        from `tabWAFD Invoice Item` ii
        inner join `tabWAFD Invoice` i on i.name = ii.parent
        where ii.parenttype = 'WAFD Invoice'
          and i.status != 'ملغاة / Cancelled'
          and ifnull(ii.meal_plan, '') != ''
    """))
    rows=[p for p in plans if p.name not in already]
    if not rows: frappe.throw("تمت فوترة جميع الكميات المسلمة / All delivered quantities are already invoiced")
    inv=frappe.get_doc({"doctype":"WAFD Invoice","project":project_name,"invoice_date":nowdate(),"due_date":due_date,"billing_basis":"الكميات المسلمة / Delivered Quantities","tax_rate":flt(tax_rate),"status":"مسودة / Draft","description":"فاتورة مبنية على الكميات المسلمة / Invoice based on delivered quantities"})
    for r in rows: inv.append("items",{"meal_plan":r.name,"service_date":r.service_date,"hotel":r.hotel,"meal_type":r.meal_type,"delivered_quantity":r.delivered_quantity,"unit_price":r.unit_price,"amount":flt(r.delivered_quantity)*flt(r.unit_price)})
    inv.insert(); return inv.name

@frappe.whitelist()
def get_dashboard_data():
    active=frappe.db.count("WAFD Catering Project", {"status":["in",["تخطيط / Planning","نشط / Active"]]})
    today=nowdate()
    planned=frappe.db.sql("select coalesce(sum(quantity),0) from `tabWAFD Meal Plan` where service_date=%s and status!='ملغي / Cancelled'",today)[0][0]
    delivered=frappe.db.sql("select coalesce(sum(received_quantity),0) from `tabWAFD Delivery Proof` where date(delivery_time)=%s and status in ('مقبول بالكامل / Fully Accepted','مقبول جزئياً / Partially Accepted')",today)[0][0]
    receivable=frappe.db.sql("select coalesce(sum(balance),0) from `tabWAFD Invoice` where status not in ('مدفوعة / Paid','ملغاة / Cancelled')",)[0][0]
    costs=frappe.db.sql("select coalesce(sum(amount),0) from `tabWAFD Project Cost` where status not in ('ملغي / Cancelled','مسودة / Draft')",)[0][0]
    revenue=frappe.db.sql("select coalesce(sum(amount),0) from `tabWAFD Payment` where status='معتمد / Confirmed'",)[0][0]
    return {"active_projects":active,"planned_meals_today":planned,"delivered_meals_today":delivered,"receivables":receivable,"actual_cost":costs,"collected_revenue":revenue,"profit":flt(revenue)-flt(costs)}
