import json
import frappe

LOGO = "/assets/wafd_one/images/wafd-almadinah-official.png"
GOLD = "#b88a2a"
LIGHT_GRAY = "#e7e7e7"
BORDER = "#bdbdbd"


def _block(block_id, block_type, x, y, w, h, html="", **kwargs):
    row = {"id": block_id, "type": block_type, "x": x, "y": y, "w": w, "h": h,
           "z": kwargs.pop("z", 1), "html": html, "font_family": "Arial",
           "font_size": kwargs.pop("font_size", 12), "color": kwargs.pop("color", "#111111"),
           "background": kwargs.pop("background", "transparent"), "opacity": 1, "rotation": 0}
    row.update(kwargs)
    return row


def _header(title_ar, title_en, body):
    blocks = [
        _block("logo", "logo", 675, 18, 70, 70, src=LOGO, z=20),
        _block("company_contact", "text", 48, 24, 245, 58,
            '<div style="direction:rtl;text-align:left;font-size:9.5px;line-height:1.7;color:#555;">'
            '<div>المدينة المنورة — حي الملك فهد</div><div dir="ltr">0500336989</div>'
            '<div dir="ltr">wafd.almadinah@gmail.com</div></div>'),
        _block("brand", "text", 315, 27, 340, 58,
            '<div style="direction:rtl;text-align:right;"><div style="font-size:18px;font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>'
            '<div style="font-size:9.5px;color:#666;">WAFD AL-MADINAH CATERING SERVICES</div></div>'),
        _block("header_line", "line", 48, 96, 697, 2, background=GOLD, color=GOLD),
        _block("title", "text", 48, 110, 697, 48,
            f'<div style="text-align:center;font-size:22px;font-weight:700;">{title_ar}</div>'
            f'<div style="text-align:center;font-size:10px;color:#666;">{title_en}</div>'),
    ]
    blocks.extend(body)
    return {"version": 4, "blocks": blocks}


def _info_table(rows):
    out=['<table style="width:100%;table-layout:fixed;border-collapse:collapse;direction:rtl;font-size:10.5px;">']
    for row in rows:
        out.append('<tr>')
        for label,value in row:
            out.append(f'<td style="border:1px solid {BORDER};padding:6px;vertical-align:top;"><b>{label}</b><br>{value}</td>')
        out.append('</tr>')
    out.append('</table>')
    return ''.join(out)


def invoice_canvas():
    meta=_info_table([
        [("رقم الفاتورة / Invoice No.",'<span dir="ltr">{{ doc.name or "" }}</span>'),
         ("تاريخ الفاتورة / Invoice Date",'{{ frappe.utils.formatdate(doc.invoice_date) if doc.invoice_date else "" }}'),
         ("تاريخ الاستحقاق / Due Date",'{{ frappe.utils.formatdate(doc.due_date) if doc.due_date else "" }}')],
        [("المشروع / Project",'<span dir="ltr">{{ doc.project or "" }}</span>'),
         ("أساس الفوترة / Billing Basis",'{{ doc.billing_basis or "" }}'),
         ("الحالة / Status",'{{ doc.status or "" }}')],
    ])
    items=(f'<table style="width:100%;table-layout:fixed;font-size:9.5px;border-collapse:collapse;direction:rtl;">'
        f'<thead><tr style="background:{LIGHT_GRAY};color:#222;">'
        f'<th style="width:4%;padding:6px 2px;border:1px solid {BORDER};">#</th>'
        f'<th style="width:17%;padding:6px 2px;border:1px solid {BORDER};">الخدمة<br><small>Service</small></th>'
        f'<th style="width:14%;padding:6px 2px;border:1px solid {BORDER};">التاريخ<br><small>Date</small></th>'
        f'<th style="width:20%;padding:6px 2px;border:1px solid {BORDER};">الفندق<br><small>Hotel</small></th>'
        f'<th style="width:10%;padding:6px 2px;border:1px solid {BORDER};">الكمية<br><small>Qty</small></th>'
        f'<th style="width:17%;padding:6px 2px;border:1px solid {BORDER};">سعر الوحدة<br><small>Unit Price</small></th>'
        f'<th style="width:18%;padding:6px 2px;border:1px solid {BORDER};">الإجمالي<br><small>Amount</small></th></tr></thead><tbody>'
        '{% for row in (doc.items or []) %}<tr><td style="padding:6px 2px;border:1px solid #bbb;text-align:center;">{{ loop.index }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;">{{ row.meal_type or row.meal_plan or "" }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;">{{ frappe.utils.formatdate(row.service_date) if row.service_date else "" }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;">{{ row.hotel or "" }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;">{{ row.delivered_quantity or 0 }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;white-space:nowrap;">{{ frappe.utils.fmt_money(row.unit_price or 0, currency="SAR") }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;white-space:nowrap;">{{ frappe.utils.fmt_money(row.amount or 0, currency="SAR") }}</td></tr>{% endfor %}'
        '{% if not doc.items %}<tr><td colspan="7" style="padding:12px;border:1px solid #bbb;text-align:center;color:#777;">لا توجد بنود / No items</td></tr>{% endif %}</tbody></table>')
    totals=('<table style="width:100%;font-size:11px;border-collapse:collapse;direction:rtl;">'
        '<tr><td style="padding:5px;border-bottom:1px solid #ddd;">المجموع قبل الضريبة / Subtotal</td><td style="padding:5px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.subtotal or 0, currency="SAR") }}</td></tr>'
        '<tr><td style="padding:5px;border-bottom:1px solid #ddd;">الضريبة {{ doc.tax_rate or 0 }}% / VAT</td><td style="padding:5px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.tax_amount or 0, currency="SAR") }}</td></tr>'
        '<tr style="font-size:14px;font-weight:700;background:#f0e5c9;"><td style="padding:7px;">الإجمالي / Grand Total</td><td style="padding:7px;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.grand_total or 0, currency="SAR") }}</td></tr>'
        '<tr><td style="padding:5px;">المحصل / Paid</td><td style="padding:5px;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.paid_amount or 0, currency="SAR") }}</td></tr>'
        '<tr><td style="padding:5px;font-weight:700;">الرصيد / Balance</td><td style="padding:5px;text-align:left;font-weight:700;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.balance or 0, currency="SAR") }}</td></tr></table>')
    return _header("فاتورة ضريبية","TAX INVOICE",[
        _block("meta","field",48,170,697,96,meta),
        _block("description","field",48,278,697,40,'<div style="direction:rtl;border:1px solid #ddd;background:#fafafa;padding:7px;font-size:10.5px;"><b>البيان / Description:</b> {{ doc.description or "فاتورة مبنية على الكميات المسلمة فعلياً" }}</div>'),
        _block("items","field",48,330,697,292,items),
        _block("notes","text",48,635,320,88,'<div style="direction:rtl;font-size:9.5px;line-height:1.6;border:1px solid #ddd;padding:8px;"><b>ملاحظات / Notes</b><br>تم إصدار هذه الفاتورة بناءً على الكميات المسلمة والمعتمدة في النظام.<br><span dir="ltr">Generated from approved delivered quantities.</span></div>'),
        _block("totals","field",390,635,355,142,totals),
        _block("status","field",48,790,697,34,'<div style="direction:rtl;text-align:center;font-size:10.5px;border:1px solid #b88a2a;padding:7px;"><b>حالة الفاتورة / Status:</b> {{ doc.status or "" }}</div>'),
    ])


def undertaking_canvas():
    intro=('<div style="direction:rtl;text-align:justify;font-size:12px;line-height:1.8;"><p>نحن <b>{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }}</b>، سجل تجاري رقم <b>{{ doc.company_cr or "7051832694" }}</b>، نتعهد بتقديم خدمات الإعاشة للمستفيدين في فندق <b>{{ doc.hotel or "................" }}</b>، وفق البيانات والشروط الموضحة أدناه، مع الالتزام بالاشتراطات الصحية والتنظيمية وجودة وسلامة الوجبات أثناء التجهيز والنقل والتسليم.</p></div>')
    details=_info_table([
        [("رقم التعهد / Undertaking No.",'<span dir="ltr">{{ doc.name or "" }}</span>'),("التاريخ / Date",'{{ frappe.utils.formatdate(doc.undertaking_date) if doc.undertaking_date else "" }}')],
        [("المشروع / Project",'{{ doc.project or "" }}'),("الفندق / Hotel",'{{ doc.hotel or "" }}')],
        [("البعثة أو العميل / Mission or Client",'{{ doc.mission or doc.second_party_name or "" }}'),("عدد المستفيدين / Beneficiaries",'{{ doc.beneficiary_count or 0 }}')],
        [("الجنسية / Nationality",'{{ doc.nationality or "" }}'),("مدة الخدمة / Service Period",'{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}')],
        [("الوجبات / Meals",'{{ doc.meal_types or "" }}'),("موقع التوريد / Supply Location",'{{ doc.supply_location or doc.hotel or "" }}')],
    ])
    return _header("تعهد والتزام إعاشة","CATERING SERVICES UNDERTAKING",[
        _block("intro","field",54,168,685,180,intro), _block("details","field",48,360,697,265,details),
        _block("terms","field",60,610,675,170,'<div style="direction:rtl;border:1px solid #ddd;padding:9px;font-size:9.4px;line-height:1.55;"><b>الشروط والملاحظات</b><ol style="margin:5px 18px 0 0;padding:0;"><li>تقديم الوجبات المتفق عليها وفق العدد ونوع الوجبة والفترة الموضحة في التعهد.</li><li>الالتزام بمواعيد تجهيز ونقل وتسليم الوجبات دون تأخير.</li><li>الالتزام باشتراطات سلامة الغذاء والنظافة والتعبئة والنقل والحفظ الحراري.</li><li>تسليم الوجبات في موقع التوريد المحدد وبالكميات المعتمدة.</li><li>تزويد الفندق بالمستندات النظامية المطلوبة عند الطلب.</li><li>للفندق التحقق من الكميات والحالة الظاهرية عند الاستلام وإثبات أي ملاحظة فوراً.</li><li>لا يُعتد بأي تعديل في العدد أو المواعيد إلا بعد اعتماده من الشركة.</li></ol>{% if doc.additional_terms or doc.service_notes %}<div style="margin-top:5px;"><b>بنود إضافية:</b> {{ doc.additional_terms or doc.service_notes }}</div>{% endif %}</div>'),
        _block("signatory","field",70,790,285,82,'<div style="direction:rtl;text-align:center;font-size:10.5px;line-height:1.7;"><b>شركة وفد المدينة لخدمات الإعاشة</b><br>{{ doc.authorized_signatory or doc.company_representative or "الممثل المعتمد" }}<br>{{ doc.signatory_title or "" }}<br>التوقيع: ____________________</div>'),
        _block("signature","signature",395,785,140,90,src='{{ doc.signature_image or "" }}',z=10),
        _block("stamp","stamp",550,770,165,120,src='{{ doc.company_stamp or "" }}',z=10),
    ])


LEGACY_UNDERTAKING_HTML = """{% set logo = doc.company_logo or '/assets/wafd_one/images/wafd-almadinah-official.png' %}
<style>
@page { size:A4; margin:8mm 14mm; }
html,body,.print-format{margin:0!important;padding:0!important;background:#fff!important;}
.sheet{direction:rtl;font-family:Tahoma,Arial,sans-serif;color:#111;font-size:10.2px;line-height:1.55;box-sizing:border-box;min-height:274mm;padding:0 1mm;page-break-inside:avoid;}
.head{display:table;width:100%;table-layout:fixed;border-bottom:1px solid #b88a2a;padding-bottom:3mm;margin-bottom:4mm;}.head-left,.head-center,.head-right{display:table-cell;vertical-align:middle;}.head-left{width:34%;direction:rtl;text-align:left;font-size:8.8px;line-height:1.65;color:#555;}.head-center{width:48%;text-align:center;}.head-center b{font-size:15px;}.head-center span{font-size:8.8px;color:#666;}.head-right{width:18%;text-align:right;}.logo{width:24mm;height:25mm;object-fit:contain;}h1{text-align:center;font-size:16px;text-decoration:underline;margin:2mm 0 4mm;}p{margin:1.2mm 0;text-align:justify;}.details{width:100%;border-collapse:collapse;margin:3mm 0;font-size:9.7px;}.details td{border:1px solid #bbb;padding:2.2mm;vertical-align:top;}.terms{border:1px solid #ccc;padding:2.5mm;margin-top:3mm;}.sign{margin-top:6mm;text-align:center;page-break-inside:avoid;}.sign-grid{display:table;width:100%;table-layout:fixed;margin-top:2mm;}.sign-cell{display:table-cell;width:33%;vertical-align:middle;text-align:center;}.sign img{max-width:46mm;max-height:34mm;object-fit:contain;}
</style>
<div class='sheet'><div class='head'><div class='head-left'><div>المدينة المنورة — حي الملك فهد</div><div dir='ltr'>0500336989</div><div dir='ltr'>wafd.almadinah@gmail.com</div></div><div class='head-center'><b>شركة وفد المدينة لخدمات الإعاشة</b><br><span>WAFD AL-MADINAH CATERING SERVICES</span></div><div class='head-right'><img class='logo' src='{{ logo }}'></div></div><h1>تعهد والتزام إعاشة</h1><p>نحن <b>{{ doc.company_name or 'شركة وفد المدينة لخدمات الإعاشة' }}</b>، سجل تجاري رقم <b>{{ doc.company_cr or '7051832694' }}</b>، نتعهد بتقديم خدمات الإعاشة للمستفيدين في الفندق الموضح أدناه، وفق البيانات المعتمدة والاشتراطات الصحية والتنظيمية، مع ضمان جودة وسلامة الوجبات أثناء التجهيز والنقل والتسليم.</p><table class='details'><tr><td><b>رقم التعهد</b><br>{{ doc.name or '' }}</td><td><b>التاريخ</b><br>{{ frappe.utils.formatdate(doc.undertaking_date) if doc.undertaking_date else '' }}</td></tr><tr><td><b>المشروع</b><br>{{ doc.project or '' }}</td><td><b>الفندق</b><br>{{ doc.hotel or '' }}</td></tr><tr><td><b>البعثة أو العميل</b><br>{{ doc.mission or doc.second_party_name or '' }}</td><td><b>عدد المستفيدين</b><br>{{ doc.beneficiary_count or 0 }}</td></tr><tr><td><b>الجنسية</b><br>{{ doc.nationality or '' }}</td><td><b>مدة الخدمة</b><br>{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else '' }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else '' }}</td></tr><tr><td><b>الوجبات</b><br>{{ doc.meal_types or '' }}</td><td><b>موقع التوريد</b><br>{{ doc.supply_location or doc.hotel or '' }}</td></tr></table><div class='terms'><b>الشروط والملاحظات:</b><br><ol style='margin:1mm 5mm 0 0;padding:0'><li>تقديم الوجبات المتفق عليها وفق العدد ونوع الوجبة والفترة الموضحة في التعهد.</li><li>الالتزام بمواعيد تجهيز ونقل وتسليم الوجبات دون تأخير.</li><li>الالتزام باشتراطات سلامة الغذاء والنظافة والتعبئة والنقل والحفظ الحراري.</li><li>تسليم الوجبات في موقع التوريد المحدد وبالكميات المعتمدة.</li><li>تزويد الفندق بالمستندات النظامية المطلوبة عند الطلب.</li><li>للفندق التحقق من الكميات والحالة الظاهرية عند الاستلام وإثبات أي ملاحظة فوراً.</li><li>لا يُعتد بأي تعديل في العدد أو المواعيد إلا بعد اعتماده من الشركة.</li></ol>{% if doc.additional_terms or doc.service_notes %}<div><b>بنود إضافية:</b> {{ doc.additional_terms or doc.service_notes }}</div>{% endif %}</div><div class='sign'><b>شركة وفد المدينة لخدمات الإعاشة</b><br>{{ doc.authorized_signatory or doc.company_representative or 'الممثل المعتمد' }}<div class='sign-grid'><div class='sign-cell'>التوقيع<br>{% if doc.signature_image %}<img src='{{ doc.signature_image }}'>{% else %}____________________{% endif %}</div><div class='sign-cell'></div><div class='sign-cell'>الختم<br>{% if doc.company_stamp %}<img src='{{ doc.company_stamp }}'>{% else %}____________________{% endif %}</div></div></div></div>"""


def execute():
    if frappe.db.exists("DocType", "WAFD Document Template"):
        for category, canvas in (("Invoice", invoice_canvas()), ("Hotel Undertaking", undertaking_canvas())):
            for name in frappe.get_all("WAFD Document Template", filters={"document_category": category}, pluck="name"):
                doc = frappe.get_doc("WAFD Document Template", name)
                doc.logo = LOGO
                doc.page_size = "A4"; doc.orientation = "Portrait"; doc.direction = "RTL"
                doc.margin_top_mm = 0; doc.margin_right_mm = 0; doc.margin_bottom_mm = 0; doc.margin_left_mm = 0
                doc.canvas_json = json.dumps(canvas, ensure_ascii=False)
                doc.save(ignore_permissions=True)
        frappe.clear_cache(doctype="WAFD Document Template")
    pf_name = "تعهد والتزام إعاشة — WAFD"
    if frappe.db.exists("Print Format", pf_name):
        frappe.db.set_value("Print Format", pf_name, {"html": LEGACY_UNDERTAKING_HTML, "custom_format": 1, "print_format_type": "Jinja"}, update_modified=False)
        frappe.clear_cache(doctype="Print Format")
