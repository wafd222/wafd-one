import frappe


def execute():
    """Repair fleet availability and delivery totals without altering valid operational records."""
    if frappe.db.table_exists("WAFD Vehicle"):
        frappe.db.sql("""update `tabWAFD Vehicle` set status='متاحة / Available'
            where status='في مهمة / On Trip' and name not in
            (select distinct vehicle from `tabWAFD Delivery Trip` where status in
            ('مخططة / Planned','تم التحميل / Loaded','في الطريق / In Transit','وصلت / Arrived','متأخرة / Delayed'))""")
    if frappe.db.table_exists("WAFD Driver"):
        frappe.db.sql("""update `tabWAFD Driver` set status='متاح / Available'
            where status='في مهمة / On Trip' and name not in
            (select distinct driver from `tabWAFD Delivery Trip` where status in
            ('مخططة / Planned','تم التحميل / Loaded','في الطريق / In Transit','وصلت / Arrived','متأخرة / Delayed'))""")
    if frappe.db.table_exists("WAFD Delivery Proof"):
        frappe.db.sql("""update `tabWAFD Delivery Proof` set delivered_quantity=received_quantity
            where coalesce(delivered_quantity,0) != coalesce(received_quantity,0)""")
