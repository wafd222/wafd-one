from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, getdate, nowdate

@frappe.whitelist()
def create_project(data):
    if isinstance(data, str): data = frappe.parse_json(data)
    required = ["project_title","contracting_entity","distribution_site","start_date","end_date","daily_meals","sale_price_per_meal"]
    missing=[x for x in required if not data.get(x)]
    if missing: frappe.throw(_("الحقول المطلوبة غير مكتملة: {0}").format(", ".join(missing)))
    doc=frappe.get_doc({"doctype":"WAFD Iftar Project", **{k:v for k,v in data.items() if k in required+['contracting_entity_type','site_details','meal_template','include_zamzam']}})
    doc.insert()
    generate_daily_operations(doc.name)
    return {"name":doc.name,"route":f"/app/wafd-iftar-project/{doc.name}"}

@frappe.whitelist()
def generate_daily_operations(project_name):
    project=frappe.get_doc("WAFD Iftar Project", project_name)
    project.check_permission("write")
    created=0
    day=getdate(project.start_date); end=getdate(project.end_date)
    while day <= end:
        if not frappe.db.exists("WAFD Iftar Daily Operation", {"project":project.name,"operation_date":day}):
            frappe.get_doc({"doctype":"WAFD Iftar Daily Operation","project":project.name,"operation_date":day,"planned_meals":project.daily_meals}).insert(ignore_permissions=True)
            created+=1
        day=add_days(day,1)
    return {"created":created}

@frappe.whitelist()
def get_project_operations(project_name):
    frappe.has_permission("WAFD Iftar Project", "read", project_name, throw=True)
    return frappe.get_all("WAFD Iftar Daily Operation", filters={"project":project_name}, fields=["name","operation_date","status","planned_meals","produced_meals","packaged_meals","loaded_meals","delivered_meals","received_meals","surplus_meals","waste_meals","completion_percent"], order_by="operation_date asc")

@frappe.whitelist()
def get_dashboard(date=None):
    date=date or nowdate()
    rows=frappe.get_all("WAFD Iftar Daily Operation", filters={"operation_date":date}, fields=["name","project","status","planned_meals","produced_meals","packaged_meals","loaded_meals","delivered_meals","received_meals","completion_percent"], order_by="modified desc")
    sums={k:sum(cint(r.get(k)) for r in rows) for k in ["planned_meals","produced_meals","packaged_meals","loaded_meals","delivered_meals","received_meals"]}
    sums['remaining_meals']=max(0,sums['planned_meals']-sums['received_meals'])
    sums['project_count']=len({r.project for r in rows})
    sums['completion_percent']=round((sums['received_meals']/sums['planned_meals']*100),1) if sums['planned_meals'] else 0
    return {"summary":sums,"rows":rows}
