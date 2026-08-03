import frappe
from wafd_one.patches.v10_0_0_rc43.execute import _save_template, LOGO

GOLD = "#b79b55"
TEXT = "#1d2025"
MUTED = "#6b6f76"


def _header(title_ar, title_en):
    return f'''<table style="width:100%;border-collapse:collapse;direction:ltr;">
<tr>
<td style="width:27%;vertical-align:top;text-align:left;font-size:9px;line-height:1.65;color:{MUTED};padding-top:5px;">
<div>المدينة المنورة — حي الملك فهد</div><div>0500336989</div><div>wafd.almadinah@gmail.com</div>
</td>
<td style="width:53%;vertical-align:middle;text-align:center;color:{TEXT};">
<div style="font-size:18px;font-weight:800;direction:rtl;">شركة وفد المدينة لخدمات الإعاشة</div>
<div style="font-size:9px;color:{MUTED};margin-top:2px;">WAFD AL-MADINAH CATERING SERVICES</div>
<div style="font-size:22px;font-weight:800;margin-top:14px;direction:rtl;">{title_ar}</div>
<div style="font-size:10px;color:{MUTED};margin-top:2px;">{title_en}</div>
</td>
<td style="width:20%;vertical-align:top;text-align:right;"><img src="{LOGO}" style="width:82px;height:76px;object-fit:contain;object-position:center;"></td>
</tr></table><div style="height:3px;background:{GOLD};margin:12px 0 18px;"></div>'''


def _details(rows):
    html = '<table style="width:100%;border-collapse:collapse;font-size:10px;direction:rtl;color:#24272c;">'
    for left, right in rows:
        html += f'''<tr>
<td style="border:1px solid #d8d4ca;background:#f7f5ef;padding:7px;width:22%;font-weight:700;">{left[0]}</td>
<td style="border:1px solid #d8d4ca;padding:7px;width:28%;">{left[1]}</td>
<td style="border:1px solid #d8d4ca;background:#f7f5ef;padding:7px;width:22%;font-weight:700;">{right[0]}</td>
<td style="border:1px solid #d8d4ca;padding:7px;width:28%;">{right[1]}</td>
</tr>'''
    return html + '</table>'


def _signature_area(delivery=False):
    receiver = '''<td style="width:50%;vertical-align:top;padding:8px;">
<div style="font-weight:700;margin-bottom:6px;">المستلم / Receiver</div>
<div>الاسم: {{ doc.receiver_name or "" }}</div><div>الصفة: {{ doc.receiver_title or "" }}</div>
{% if doc.receiver_signature %}<div style="height:68px;margin-top:8px;"><img src="{{ doc.receiver_signature }}" style="max-width:220px;max-height:68px;object-fit:contain;"></div>{% else %}<div style="height:54px;border-bottom:1px solid #777;margin-top:8px;"></div>{% endif %}
</td>''' if delivery else ''
    company_width = '50%' if delivery else '100%'
    return f'''<table style="width:100%;border-collapse:collapse;direction:rtl;font-size:10px;margin-top:20px;"><tr>
{receiver}
<td style="width:{company_width};vertical-align:top;padding:8px;">
<table style="width:100%;border-collapse:collapse;"><tr>
<td style="padding:7px;text-align:center;">إعداد / Prepared by<br><br>________________</td>
<td style="padding:7px;text-align:center;">مراجعة / Reviewed by<br><br>________________</td>
<td style="padding:7px;text-align:center;">اعتماد / Approved by<br><br>________________</td>
</tr></table></td></tr></table>'''


def _footer():
    return f'''<div style="border-top:1px solid {GOLD};margin-top:24px;padding-top:7px;text-align:center;font-size:8px;color:{MUTED};direction:rtl;">شركة وفد المدينة لخدمات الإعاشة &nbsp; | &nbsp; 0500336989 &nbsp; | &nbsp; www.wafdalmadinah.com &nbsp; | &nbsp; الرقم الضريبي: 314262038700003</div>'''


def _canvas(title_ar, title_en, rows, extra='', delivery=False):
    html = _header(title_ar, title_en) + _details(rows)
    if extra:
        html += f'<div style="margin-top:16px;border:1px solid #dfdbd0;background:#fbfaf7;padding:12px;direction:rtl;font-size:10px;line-height:1.7;">{extra}</div>'
    if delivery:
        html += '''{% if doc.hotel_stamp %}<div style="margin-top:14px;text-align:left;direction:rtl;"><div style="font-size:9px;font-weight:700;">ختم الفندق / Hotel Stamp</div><img src="{{ doc.hotel_stamp }}" style="max-width:130px;max-height:85px;object-fit:contain;"></div>{% endif %}'''
    html += _signature_area(delivery=delivery) + _footer()
    return {"page": {"width": 794, "height": 1123, "background": "#fff"}, "blocks": [{"id": "main", "type": "html", "x": 42, "y": 30, "w": 710, "h": 1015, "html": html}]}


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    _save_template("WAFD Packaging Record", "أمر التغليف", "Other", _canvas(
        "أمر التغليف", "PACKAGING ORDER",
        [
            (("المشروع / Project", '{{ doc.project or "" }}'), ("دفعة الإنتاج / Production Batch", '{{ doc.production_batch or "" }}')),
            (("خطة الوجبة / Meal Plan", '{{ doc.meal_plan or "" }}'), ("تاريخ التغليف / Packaging Date", '{{ frappe.utils.formatdate(doc.packaging_date) if doc.packaging_date else "" }}')),
            (("الكمية المخططة / Planned Qty", '{{ doc.planned_quantity or 0 }}'), ("الكمية المغلفة / Packed Qty", '{{ doc.packed_quantity or 0 }}')),
            (("عدد الصناديق / Boxes", '{{ doc.box_count or 0 }}'), ("عدد السخانات / Hot Cabinets", '{{ doc.hot_cabinet_count or 0 }}')),
        ],
        '<b>بيان التغليف:</b><div style="white-space:pre-wrap;">{{ doc.box_manifest or "" }}</div><br><b>ملاحظات:</b> {{ doc.notes or "" }}'
    ))
    _save_template("WAFD Loading Record", "أمر التحميل", "Other", _canvas(
        "أمر التحميل", "LOADING ORDER",
        [
            (("المشروع / Project", '{{ doc.project or "" }}'), ("سجل التغليف / Packaging", '{{ doc.packaging_record or "" }}')),
            (("الفندق / Hotel", '{{ doc.hotel or "" }}'), ("وقت التحميل / Loading Time", '{{ doc.loading_date or "" }}')),
            (("المركبة / Vehicle", '{{ doc.vehicle or "" }}'), ("السائق / Driver", '{{ doc.driver or "" }}')),
            (("الكمية / Quantity", '{{ doc.quantity or 0 }}'), ("عدد الصناديق / Boxes", '{{ doc.box_count or 0 }}')),
            (("عدد السخانات / Hot Cabinets", '{{ doc.hot_cabinet_count or 0 }}'), ("إجمالي السفندشات / Sandwiches", '{{ doc.hot_cabinet_sandwich_total or 0 }}')),
        ],
        '<b>حالة التحميل:</b> {{ doc.status or "" }}<br><b>رقم الختم:</b> {{ doc.seal_number or "" }}<br><b>ملاحظات:</b> {{ doc.notes or "" }}'
    ))
    _save_template("WAFD Delivery Note", "سند التسليم", "Delivery", _canvas(
        "سند التسليم", "DELIVERY NOTE",
        [
            (("المشروع / Project", '{{ doc.project or "" }}'), ("رحلة التوصيل / Trip", '{{ doc.delivery_trip or "" }}')),
            (("الفندق / Hotel", '{{ doc.hotel or "" }}'), ("وقت التسليم / Delivery Time", '{{ doc.delivery_time or "" }}')),
            (("المركبة / Vehicle", '{{ doc.vehicle or "" }}'), ("السائق / Driver", '{{ doc.driver or "" }}')),
            (("الكمية المسلمة / Delivered Qty", '{{ doc.delivered_quantity or 0 }}'), ("عدد الصناديق / Boxes", '{{ doc.box_count or 0 }}')),
            (("عدد السخانات / Hot Cabinets", '{{ doc.hot_cabinet_count or 0 }}'), ("مندوب الشركة / Company Rep.", '{{ doc.company_representative or "" }}')),
        ],
        '<b>ملاحظات:</b> {{ doc.notes or "" }}', delivery=True
    ))
    _save_template("WAFD Receiving Note", "سند الاستلام", "Delivery", _canvas(
        "سند الاستلام", "RECEIVING NOTE",
        [
            (("المشروع / Project", '{{ doc.project or "" }}'), ("سند التسليم / Delivery Note", '{{ doc.delivery_note or "" }}')),
            (("الفندق / Hotel", '{{ doc.hotel or "" }}'), ("وقت الاستلام / Receipt Time", '{{ doc.receipt_time or "" }}')),
            (("الكمية المسلمة / Delivered Qty", '{{ doc.delivered_quantity or 0 }}'), ("الكمية المستلمة / Received Qty", '{{ doc.received_quantity or 0 }}')),
            (("الكمية المرفوضة / Rejected Qty", '{{ doc.rejected_quantity or 0 }}'), ("حالة الوجبات / Condition", '{{ doc.condition_status or "" }}')),
            (("المركبة / Vehicle", '{{ doc.vehicle or "" }}'), ("السائق / Driver", '{{ doc.driver or "" }}')),
        ],
        '<b>ملاحظات:</b> {{ doc.notes or "" }}', delivery=True
    ))
    frappe.clear_cache()
