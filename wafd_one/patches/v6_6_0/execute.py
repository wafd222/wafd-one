import json
import frappe

DOCUMENTS = [
    ("تعهد الفندق", "WAFD Hotel Undertaking", "Hotel Undertaking"),
    ("العقد", "WAFD Contract", "Contract"),
    ("عرض السعر", "WAFD Contract", "Quotation"),
    ("الفاتورة", "WAFD Invoice", "Invoice"),
    ("أمر التشغيل", "WAFD Catering Project", "Operation Order"),
    ("أمر الإنتاج", "WAFD Production Batch", "Production Order"),
    ("أمر التحضير", "WAFD Meal Plan", "Preparation Order"),
    ("أمر التحميل", "WAFD Loading Record", "Loading Order"),
    ("إذن التسليم", "WAFD Delivery Proof", "Delivery Note"),
    ("شهادة شكر", "WAFD Mission", "Certificate"),
]

def _default_canvas(title, doctype):
    return {"version": 1, "blocks": [
        {"id":"logo","type":"logo","x":40,"y":25,"w":180,"h":80,"z":1,"src":"","style":""},
        {"id":"title","type":"text","x":250,"y":45,"w":320,"h":55,"z":2,"html":f'<div style="font-size:24px;font-weight:700;text-align:center">{title}</div>',"style":""},
        {"id":"docno","type":"field","x":40,"y":125,"w":260,"h":36,"z":2,"html":'<div><b>{{ _(\"Document ID\") }}:</b> {{ doc.name }}</div>',"style":"font-size:14px;"},
        {"id":"date","type":"field","x":500,"y":125,"w":230,"h":36,"z":2,"html":'<div><b>{{ _(\"Date\") }}:</b> {{ frappe.format_date(doc.creation) if doc.creation else \"\" }}</div>',"style":"font-size:14px;text-align:left;"},
        {"id":"body","type":"text","x":55,"y":190,"w":680,"h":600,"z":1,"html":f'<div style="font-size:16px;line-height:2"><p>يمكن تعديل هذا النص بالكامل من داخل مصمم المستندات.</p><p>نوع المستند: {doctype}</p><p>استخدم قائمة الحقول لإضافة بيانات المستند تلقائياً.</p></div>',"style":""},
        {"id":"signature","type":"signature","x":430,"y":880,"w":150,"h":75,"z":2,"src":"","style":""},
        {"id":"stamp","type":"stamp","x":590,"y":850,"w":120,"h":120,"z":2,"src":"","style":""},
        {"id":"company","type":"text","x":400,"y":960,"w":310,"h":45,"z":2,"html":'<div style="font-weight:700;text-align:center">شركة وفد المدينة لخدمات الإعاشة</div>',"style":""},
        {"id":"footerline","type":"line","x":40,"y":1040,"w":700,"h":15,"z":1,"style":""},
    ]}

def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    for title, doctype, category in DOCUMENTS:
        if not frappe.db.exists("DocType", doctype):
            continue
        name = frappe.db.get_value("WAFD Document Template", {"template_title": title, "reference_doctype": doctype}, "name")
        if name:
            continue
        doc = frappe.get_doc({"doctype":"WAFD Document Template","template_title":title,"reference_doctype":doctype,"document_category":category,"enabled":1,"is_default":1 if category in {"Hotel Undertaking","Contract","Invoice"} else 0,"page_size":"A4","orientation":"Portrait","direction":"RTL","margin_top_mm":8,"margin_right_mm":8,"margin_bottom_mm":8,"margin_left_mm":8,"canvas_json":json.dumps(_default_canvas(title, doctype),ensure_ascii=False)})
        doc.insert(ignore_permissions=True)
    frappe.clear_cache()
