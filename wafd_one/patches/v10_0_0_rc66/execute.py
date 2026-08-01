import frappe
from wafd_one.patches.v10_0_0_rc43.execute import _save_template, LOGO


def _receiving_canvas():
    details = '''<table style="width:100%;border-collapse:collapse;font-size:10px;direction:rtl;table-layout:fixed;">
    <tr><td class="k">المشروع / Project</td><td>{{ doc.project or "" }}</td><td class="k">سند التسليم / Delivery Note</td><td>{{ doc.delivery_note or "" }}</td></tr>
    <tr><td class="k">الفندق / Hotel</td><td>{{ doc.hotel or "" }}</td><td class="k">وقت الاستلام / Receipt Time</td><td>{{ doc.receipt_time or "" }}</td></tr>
    <tr><td class="k">الكمية المسلمة / Delivered</td><td>{{ doc.delivered_quantity or 0 }}</td><td class="k">الكمية المستلمة / Received</td><td>{{ doc.received_quantity or 0 }}</td></tr>
    <tr><td class="k">الكمية المرفوضة / Rejected</td><td>{{ doc.rejected_quantity or 0 }}</td><td class="k">حالة الوجبات / Condition</td><td>{{ doc.condition_status or "" }}</td></tr>
    </table><style>.k{background:#f7f4ed;font-weight:700}.wafd-receiving td{border:1px solid #d8d8d8;padding:7px}</style>'''
    sign = '''<div style="display:flex;gap:20px;direction:rtl;align-items:flex-end;font-size:10px;page-break-inside:avoid;">
      <div style="flex:1;line-height:1.8"><b>اسم المستلم:</b> {{ doc.receiver_name or "" }}<br><b>الصفة:</b> {{ doc.receiver_title or "" }}<br><b>ملاحظات:</b> {{ doc.notes or "" }}</div>
      <div style="width:220px;text-align:center"><b>توقيع المستلم / Signature</b><div style="height:100px;border-bottom:1px solid #777;display:flex;align-items:center;justify-content:center;overflow:hidden;">{% if doc.receiver_signature %}<img src="{{ doc.receiver_signature }}" style="max-width:205px;max-height:92px;object-fit:contain">{% endif %}</div></div>
      <div style="width:150px;text-align:center"><b>ختم الفندق / Hotel Stamp</b><div style="height:100px;display:flex;align-items:center;justify-content:center;overflow:hidden;">{% if doc.hotel_stamp %}<img src="{{ doc.hotel_stamp }}" style="max-width:140px;max-height:92px;object-fit:contain">{% endif %}</div></div>
    </div>'''
    return {
        "page": {"width": 794, "height": 1123, "background": "#fff"},
        "blocks": [
            {"id":"header","type":"html","x":34,"y":24,"w":726,"h":90,"html":f'<div style="border-bottom:2px solid #b38a3e;padding-bottom:8px;text-align:center;direction:rtl"><img src="{LOGO}" style="position:absolute;right:0;top:0;width:68px;height:64px;object-fit:contain"><b style="font-size:17px">شركة وفد المدينة لخدمات الإعاشة</b><div style="font-size:9px;color:#777">WAFD AL MADINAH CATERING SERVICES</div><h2 style="margin:9px 0 0">سند استلام</h2><div style="font-size:10px">RECEIVING NOTE</div></div>'},
            {"id":"details","type":"html","x":34,"y":126,"w":726,"h":250,"html":f'<div class="wafd-receiving">{details}</div>'},
            {"id":"signature","type":"html","x":34,"y":405,"w":726,"h":190,"html":sign},
            {"id":"footer","type":"html","x":34,"y":755,"w":726,"h":30,"html":'<div style="border-top:1px solid #b38a3e;text-align:center;font-size:8px;padding-top:6px;direction:rtl">0500336989 &nbsp; | &nbsp; wafd.almadinah@gmail.com &nbsp; | &nbsp; CR 7051832694</div>'},
        ],
    }


def execute():
    frappe.db.set_value(
        "DocField",
        {"parent": "WAFD Project Service", "fieldname": "meal_name"},
        {"fieldtype": "Link", "options": "WAFD Recipe", "reqd": 1},
        update_modified=False,
    )
    if frappe.db.exists("DocType", "WAFD Document Template"):
        _save_template("WAFD Receiving Note", "سند الاستلام الاحترافي", "Delivery", _receiving_canvas())
    frappe.clear_cache()
