import json
import frappe

# RC37: company contact moved to header; all bottom footers removed.

LOGO = "/assets/wafd_one/images/wafd-almadinah-official.png"
GOLD = "#b88a2a"
DARK = "#1f1f1f"


def b(block_id, block_type, x, y, w, h, html="", **kwargs):
    data = {
        "id": block_id, "type": block_type, "x": x, "y": y, "w": w, "h": h,
        "z": kwargs.pop("z", 1), "html": html, "font_family": "Arial",
        "font_size": kwargs.pop("font_size", 12), "color": kwargs.pop("color", "#111111"),
        "background": kwargs.pop("background", "transparent"), "opacity": 1, "rotation": 0,
    }
    data.update(kwargs)
    return data


def shell(title_ar, title_en, body_blocks):
    blocks = [
        b("logo", "logo", 675, 22, 70, 66, src=LOGO, z=20),
        b("company_contact", "text", 48, 24, 250, 64,
          '<div style="direction:rtl;text-align:left;font-size:9.5px;line-height:1.65;color:#555;">'
          '<div style="font-weight:700;color:#222;">بيانات الشركة / Company Details</div>'
          '<div>المدينة المنورة — حي الملك فهد</div>'
          '<div dir="ltr">0500336989</div>'
          '<div dir="ltr">wafd.almadinah@gmail.com</div></div>'),
        b("brand", "text", 315, 27, 340, 58,
          '<div style="direction:rtl;text-align:right;">'
          '<div style="font-size:18px;font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>'
          '<div style="font-size:9.5px;color:#666;letter-spacing:.2px;">WAFD AL-MADINAH CATERING SERVICES</div></div>'),
        b("header_line", "line", 48, 96, 697, 2, background=GOLD, color=GOLD),
        b("title", "text", 48, 112, 697, 50,
          f'<div style="text-align:center;font-size:23px;font-weight:700;">{title_ar}</div>'
          f'<div style="text-align:center;font-size:10.5px;color:#666;">{title_en}</div>'),
    ]
    blocks.extend(body_blocks)
    return {"version": 4, "blocks": blocks}


def info_table(rows):
    html = ['<table style="width:100%;table-layout:fixed;border-collapse:collapse;direction:rtl;font-size:11px;">']
    for row in rows:
        html.append('<tr>')
        for label, value in row:
            html.append(f'<td style="border:1px solid #d5d5d5;padding:7px;vertical-align:top;"><b>{label}</b><br>{value}</td>')
        html.append('</tr>')
    html.append('</table>')
    return ''.join(html)


def invoice_canvas():
    meta = info_table([
        [("رقم الفاتورة / Invoice No.", '<span dir="ltr">{{ doc.name or "" }}</span>'),
         ("تاريخ الفاتورة / Invoice Date", '{{ frappe.utils.formatdate(doc.invoice_date) if doc.invoice_date else "" }}'),
         ("تاريخ الاستحقاق / Due Date", '{{ frappe.utils.formatdate(doc.due_date) if doc.due_date else "" }}')],
        [("المشروع / Project", '<span dir="ltr">{{ doc.project or "" }}</span>'),
         ("أساس الفوترة / Billing Basis", '{{ doc.billing_basis or "" }}'),
         ("الحالة / Status", '{{ doc.status or "" }}')],
    ])
    items = ('<table style="width:100%;table-layout:fixed;font-size:9.5px;border-collapse:collapse;direction:rtl;">'
        '<thead><tr style="background:#222;color:#fff;">'
        '<th style="width:4%;padding:6px 2px;border:1px solid #555;">#</th>'
        '<th style="width:17%;padding:6px 2px;border:1px solid #555;">الخدمة<br><small>Service</small></th>'
        '<th style="width:14%;padding:6px 2px;border:1px solid #555;">التاريخ<br><small>Date</small></th>'
        '<th style="width:20%;padding:6px 2px;border:1px solid #555;">الفندق<br><small>Hotel</small></th>'
        '<th style="width:10%;padding:6px 2px;border:1px solid #555;">الكمية<br><small>Qty</small></th>'
        '<th style="width:17%;padding:6px 2px;border:1px solid #555;">سعر الوحدة<br><small>Unit Price</small></th>'
        '<th style="width:18%;padding:6px 2px;border:1px solid #555;">الإجمالي<br><small>Amount</small></th></tr></thead><tbody>'
        '{% for row in (doc.items or []) %}<tr>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;">{{ loop.index }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;">{{ row.meal_type or row.meal_plan or "" }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;">{{ frappe.utils.formatdate(row.service_date) if row.service_date else "" }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;">{{ row.hotel or "" }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;">{{ row.delivered_quantity or 0 }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;white-space:nowrap;">{{ frappe.utils.fmt_money(row.unit_price or 0, currency="SAR") }}</td>'
        '<td style="padding:6px 2px;border:1px solid #bbb;text-align:center;white-space:nowrap;">{{ frappe.utils.fmt_money(row.amount or 0, currency="SAR") }}</td></tr>{% endfor %}'
        '{% if not doc.items %}<tr><td colspan="7" style="padding:14px;border:1px solid #bbb;text-align:center;color:#777;">لا توجد بنود / No items</td></tr>{% endif %}'
        '</tbody></table>')
    totals = ('<table style="width:100%;font-size:11px;border-collapse:collapse;direction:rtl;">'
        '<tr><td style="padding:6px;border-bottom:1px solid #ddd;">المجموع قبل الضريبة / Subtotal</td><td style="padding:6px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.subtotal or 0, currency="SAR") }}</td></tr>'
        '<tr><td style="padding:6px;border-bottom:1px solid #ddd;">الضريبة {{ doc.tax_rate or 0 }}% / VAT</td><td style="padding:6px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.tax_amount or 0, currency="SAR") }}</td></tr>'
        '<tr style="font-size:14px;font-weight:700;background:#f0e5c9;"><td style="padding:8px;">الإجمالي / Grand Total</td><td style="padding:8px;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.grand_total or 0, currency="SAR") }}</td></tr>'
        '<tr><td style="padding:6px;">المحصل / Paid</td><td style="padding:6px;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.paid_amount or 0, currency="SAR") }}</td></tr>'
        '<tr><td style="padding:6px;font-weight:700;">الرصيد / Balance</td><td style="padding:6px;text-align:left;font-weight:700;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.balance or 0, currency="SAR") }}</td></tr></table>')
    return shell("فاتورة ضريبية", "TAX INVOICE", [
        b("meta", "field", 48, 174, 697, 100, meta),
        b("description", "field", 48, 288, 697, 43, '<div style="direction:rtl;border:1px solid #ddd;background:#fafafa;padding:8px;font-size:11px;"><b>البيان / Description:</b> {{ doc.description or "فاتورة مبنية على الكميات المسلمة فعلياً" }}</div>'),
        b("items", "field", 48, 345, 697, 310, items),
        b("notes", "text", 48, 672, 320, 102, '<div style="direction:rtl;font-size:10px;line-height:1.7;border:1px solid #ddd;padding:9px;"><b>ملاحظات / Notes</b><br>تم إصدار هذه الفاتورة بناءً على الكميات المسلمة والمعتمدة في النظام.<br><span dir="ltr">Generated from approved delivered quantities.</span></div>'),
        b("totals", "field", 390, 672, 355, 150, totals),
        b("status", "field", 48, 820, 697, 38, '<div style="direction:rtl;text-align:center;font-size:11px;border:1px solid #b88a2a;padding:8px;"><b>حالة الفاتورة / Status:</b> {{ doc.status or "" }}</div>'),
    ])


def undertaking_canvas():
    body = ('<div style="direction:rtl;text-align:justify;font-size:13px;line-height:2.05;">'
        '<p>نحن <b>{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }}</b>، سجل تجاري رقم <b>{{ doc.company_cr or "7051832694" }}</b>، '
        'نتعهد بتقديم خدمات الإعاشة للمستفيدين في فندق <b>{{ doc.hotel or "................" }}</b> وفق البيانات الموضحة أدناه، '
        'وبالالتزام بالاشتراطات الصحية والتنظيمية المعمول بها، وجودة وسلامة الوجبات أثناء التجهيز والنقل والتسليم.</p>'
        '<p>ويصدر هذا التعهد من طرف واحد من شركة وفد المدينة لخدمات الإعاشة، ويُعتمد بتوقيع ممثل الشركة وختمها.</p></div>')
    details = info_table([
        [("التاريخ / Date", '{{ frappe.utils.formatdate(doc.undertaking_date) if doc.undertaking_date else "" }}'),
         ("المشروع / Project", '{{ doc.project or "" }}')],
        [("البعثة أو العميل / Mission or Client", '{{ doc.mission or "" }}'),
         ("الفندق / Hotel", '{{ doc.hotel or "" }}')],
        [("عدد المستفيدين / Beneficiaries", '{{ doc.beneficiary_count or 0 }}'),
         ("الجنسية / Nationality", '{{ doc.nationality or "" }}')],
        [("مدة الخدمة / Service Period", '{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}'),
         ("موقع التوريد / Supply Location", '{{ doc.supply_location or "" }}')],
        [("الوجبات / Meals", '{{ doc.meal_types or "" }}'),
         ("الحالة / Status", '{{ doc.status or "" }}')],
    ])
    return shell("تعهد تقديم خدمات الإعاشة", "CATERING SERVICES UNDERTAKING", [
        b("docno", "field", 48, 166, 697, 36, '<div style="direction:rtl;font-size:10px;color:#666;text-align:left;">رقم التعهد / Undertaking No.: <span dir="ltr">{{ doc.name or "" }}</span></div>'),
        b("body", "field", 58, 214, 677, 210, body),
        b("details", "field", 48, 440, 697, 270, details),
        b("terms", "field", 48, 700, 697, 82, '<div style="direction:rtl;border:1px solid #ddd;padding:10px;font-size:11px;line-height:1.75;"><b>بنود وملاحظات إضافية / Additional Terms</b><br>{{ doc.additional_terms or doc.service_notes or "لا يوجد" }}</div>'),
        b("signatory", "field", 48, 800, 300, 95, '<div style="direction:rtl;text-align:center;font-size:11px;line-height:1.8;"><b>شركة وفد المدينة لخدمات الإعاشة</b><br>{{ doc.authorized_signatory or doc.company_representative or "الممثل المعتمد" }}<br>{{ doc.signatory_title or "" }}<br>التوقيع: ____________________</div>'),
        b("signature", "signature", 395, 795, 140, 82, src='{{ doc.signature_image or "" }}', z=10),
        b("stamp", "stamp", 565, 785, 130, 110, src='{{ doc.company_stamp or "" }}', z=10),
    ])


def generic_operational(title_ar, title_en, rows, extra_html=""):
    return shell(title_ar, title_en, [
        b("docno", "field", 48, 168, 697, 34, '<div style="direction:rtl;text-align:left;font-size:10px;color:#666;">رقم المستند / Document No.: <span dir="ltr">{{ doc.name or "" }}</span></div>'),
        b("details", "field", 48, 214, 697, 330, info_table(rows)),
        b("extra", "field", 48, 552, 697, 250, extra_html or '<div style="direction:rtl;border:1px solid #ddd;padding:12px;font-size:11px;line-height:1.8;"><b>ملاحظات / Notes</b><br>{{ doc.notes or "" }}</div>'),
        b("approval", "text", 48, 820, 697, 72, '<table style="width:100%;direction:rtl;font-size:11px;"><tr><td style="text-align:center;">أعده / Prepared by<br><br>________________</td><td style="text-align:center;">راجعه / Reviewed by<br><br>________________</td><td style="text-align:center;">اعتمده / Approved by<br><br>________________</td></tr></table>'),
    ])


def canvases():
    return {
        "Invoice": invoice_canvas(),
        "Hotel Undertaking": undertaking_canvas(),
        "Contract": generic_operational("عقد خدمات الإعاشة", "CATERING SERVICES CONTRACT", [
            [("عنوان العقد / Contract Title", '{{ doc.contract_title or "" }}'), ("رقم العقد / Contract No.", '{{ doc.contract_number or doc.name or "" }}')],
            [("البعثة أو العميل / Mission or Client", '{{ doc.mission or "" }}'), ("الفندق / Hotel", '{{ doc.hotel or "" }}')],
            [("الفترة / Period", '{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}'), ("عدد المستفيدين / Beneficiaries", '{{ doc.beneficiary_count or 0 }}')],
            [("القيمة قبل الضريبة / Before VAT", '{{ frappe.utils.fmt_money(doc.contract_value or 0, currency=doc.currency or "SAR") }}'), ("الإجمالي / Grand Total", '{{ frappe.utils.fmt_money(doc.grand_total or 0, currency=doc.currency or "SAR") }}')],
            [("شروط السداد / Payment Terms", '{{ doc.payment_terms or "" }}'), ("الحالة / Status", '{{ doc.status or "" }}')],
        ], '<div style="direction:rtl;border:1px solid #ddd;padding:12px;font-size:11px;line-height:1.8;"><b>الخدمات وتعليمات التسليم / Services & Delivery Instructions</b><br>{{ doc.delivery_instructions or doc.hotel_notes or "" }}</div>'),
        "Quotation": generic_operational("عرض سعر خدمات الإعاشة", "CATERING SERVICES QUOTATION", [
            [("العميل / Client", '{{ doc.mission or "" }}'), ("الفندق / Hotel", '{{ doc.hotel or "" }}')],
            [("عدد المستفيدين / Beneficiaries", '{{ doc.beneficiary_count or 0 }}'), ("الفترة / Period", '{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}')],
            [("إجمالي الخدمات / Services Subtotal", '{{ frappe.utils.fmt_money(doc.services_subtotal or doc.contract_value or 0, currency=doc.currency or "SAR") }}'), ("الضريبة / VAT", '{{ frappe.utils.fmt_money(doc.tax_amount or 0, currency=doc.currency or "SAR") }}')],
            [("الإجمالي شامل الضريبة / Grand Total", '{{ frappe.utils.fmt_money(doc.grand_total or 0, currency=doc.currency or "SAR") }}'), ("طريقة السداد / Payment Method", '{{ doc.payment_method or "" }}')],
        ]),
        "Operation Order": generic_operational("أمر تشغيل مشروع", "PROJECT OPERATION ORDER", [
            [("المشروع / Project", '{{ doc.project_name or doc.name or "" }}'), ("رمز المشروع / Code", '{{ doc.project_code or "" }}')],
            [("العميل / Client", '{{ doc.mission or "" }}'), ("الفندق / Hotel", '{{ doc.primary_hotel or "" }}')],
            [("الفترة / Period", '{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}'), ("المستفيدون / Beneficiaries", '{{ doc.beneficiary_count or 0 }}')],
            [("مدير المشروع / Project Manager", '{{ doc.project_manager or "" }}'), ("مدير العمليات / Operations Manager", '{{ doc.operations_manager or "" }}')],
            [("المطبخ / Kitchen", '{{ doc.default_kitchen or "" }}'), ("الأولوية / Priority", '{{ doc.operation_priority or "" }}')],
        ]),
        "Production Order": generic_operational("أمر إنتاج", "PRODUCTION ORDER", [
            [("المشروع / Project", '{{ doc.project or "" }}'), ("تاريخ الإنتاج / Date", '{{ frappe.utils.formatdate(doc.batch_date) if doc.batch_date else "" }}')],
            [("خطة الوجبة / Meal Plan", '{{ doc.meal_plan or "" }}'), ("الوصفة / Recipe", '{{ doc.recipe or "" }}')],
            [("الكمية المخططة / Planned Qty", '{{ doc.planned_quantity or 0 }}'), ("الكمية المنتجة / Produced Qty", '{{ doc.produced_quantity or 0 }}')],
            [("المطبخ / Kitchen", '{{ doc.kitchen or "" }}'), ("المشرف / Supervisor", '{{ doc.production_supervisor or "" }}')],
            [("حالة المواد / Materials", '{{ doc.materials_status or "" }}'), ("حالة الجودة / Quality", '{{ doc.quality_status or "" }}')],
        ], '<div style="direction:rtl;border:1px solid #ddd;padding:12px;font-size:11px;line-height:1.8;"><b>التتبع والإفراج الغذائي / Traceability & Food Safety</b><br>رمز التتبع: {{ doc.traceability_code or "" }}<br>حالة الإفراج: {{ doc.food_safety_release_status or "" }}<br>ملاحظات: {{ doc.notes or "" }}</div>'),
        "Preparation Order": generic_operational("أمر تحضير وجبة", "MEAL PREPARATION ORDER", [
            [("المشروع / Project", '{{ doc.project or "" }}'), ("الفندق / Hotel", '{{ doc.hotel or "" }}')],
            [("تاريخ الخدمة / Service Date", '{{ frappe.utils.formatdate(doc.service_date) if doc.service_date else "" }}'), ("وقت الخدمة / Service Time", '{{ doc.service_time or "" }}')],
            [("نوع الوجبة / Meal Type", '{{ doc.meal_type or "" }}'), ("المنيو / Menu", '{{ doc.menu_name or "" }}')],
            [("الوصفة / Recipe", '{{ doc.recipe or "" }}'), ("الكمية / Quantity", '{{ doc.quantity or 0 }}')],
            [("الحالة / Status", '{{ doc.status or "" }}'), ("القيمة / Value", '{{ frappe.utils.fmt_money(doc.total_value or 0, currency="SAR") }}')],
        ]),
        "Loading Order": generic_operational("أمر تحميل ونقل", "LOADING & DISPATCH ORDER", [
            [("المشروع / Project", '{{ doc.project or "" }}'), ("الفندق / Hotel", '{{ doc.hotel or "" }}')],
            [("وقت التحميل / Loading Time", '{{ frappe.utils.format_datetime(doc.loading_date) if doc.loading_date else "" }}'), ("وقت الخروج / Dispatch Time", '{{ frappe.utils.format_datetime(doc.dispatch_time) if doc.dispatch_time else "" }}')],
            [("المركبة / Vehicle", '{{ doc.vehicle or "" }}'), ("السائق / Driver", '{{ doc.driver or "" }}')],
            [("الكمية / Quantity", '{{ doc.quantity or 0 }}'), ("عدد الصناديق / Boxes", '{{ doc.box_count or 0 }}')],
            [("درجة الحرارة / Temperature", '{{ doc.temperature_at_loading or "" }}'), ("رقم الختم / Seal No.", '{{ doc.seal_number or "" }}')],
        ]),
        "Delivery Note": generic_operational("إذن وإثبات تسليم", "DELIVERY NOTE & PROOF", [
            [("المشروع / Project", '{{ doc.project or "" }}'), ("الفندق / Hotel", '{{ doc.hotel or "" }}')],
            [("وقت التسليم / Delivery Time", '{{ frappe.utils.format_datetime(doc.delivery_time) if doc.delivery_time else "" }}'), ("الحالة / Status", '{{ doc.status or "" }}')],
            [("الكمية المسلمة / Delivered Qty", '{{ doc.delivered_quantity or doc.received_quantity or 0 }}'), ("المرفوض / Rejected Qty", '{{ doc.rejected_quantity or 0 }}')],
            [("المستلم / Receiver", '{{ doc.receiver_name or "" }}'), ("الجوال / Mobile", '{{ doc.receiver_mobile or "" }}')],
            [("الموقع / Location", '{{ doc.latitude or "" }}, {{ doc.longitude or "" }}'), ("رحلة التوصيل / Trip", '{{ doc.delivery_trip or "" }}')],
        ], '<div style="direction:rtl;border:1px solid #ddd;padding:12px;font-size:11px;line-height:1.8;"><b>إقرار الاستلام / Receipt Acknowledgement</b><br>أقر باستلام الكميات الموضحة أعلاه بالحالة المبينة.<br><br>اسم المستلم: {{ doc.receiver_name or "" }} &nbsp;&nbsp; التوقيع: ____________________<br>ملاحظات: {{ doc.notes or "" }}</div>'),
        "Certificate": generic_operational("شهادة شكر وتقدير", "CERTIFICATE OF APPRECIATION", [
            [("الجهة / Organization", '{{ doc.official_name or doc.mission_name or "" }}'), ("الدولة / Country", '{{ doc.country or "" }}')],
            [("الموسم / Season", '{{ doc.hajj_season or "" }}'), ("التاريخ / Date", '{{ frappe.utils.formatdate(doc.modified) if doc.modified else "" }}')],
        ], '<div style="direction:rtl;text-align:center;font-size:16px;line-height:2.2;padding:30px 40px;">تتقدم الجهة المذكورة بخالص الشكر والتقدير إلى <b>شركة وفد المدينة لخدمات الإعاشة</b> نظير ما قدمته من خدمات إعاشة متميزة، سائلين الله لها دوام التوفيق والنجاح.<br><span dir="ltr" style="font-size:12px;">With sincere appreciation for the distinguished catering services provided.</span></div>'),
    }


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    mapping = canvases()
    definitions = {
        "Hotel Undertaking": ("تعهد الفندق", "WAFD Hotel Undertaking"),
        "Contract": ("العقد", "WAFD Contract"),
        "Quotation": ("عرض السعر", "WAFD Contract"),
        "Invoice": ("الفاتورة", "WAFD Invoice"),
        "Operation Order": ("أمر التشغيل", "WAFD Catering Project"),
        "Production Order": ("أمر الإنتاج", "WAFD Production Batch"),
        "Preparation Order": ("أمر التحضير", "WAFD Meal Plan"),
        "Loading Order": ("أمر التحميل", "WAFD Loading Record"),
        "Delivery Note": ("إذن التسليم", "WAFD Delivery Proof"),
        "Certificate": ("شهادة شكر", "WAFD Mission"),
    }
    for category, (title, doctype) in definitions.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        name = frappe.db.get_value("WAFD Document Template", {"document_category": category, "reference_doctype": doctype}, "name")
        if not name:
            stable = "WDT-" + category.upper().replace(" ", "-")
            doc = frappe.get_doc({
                "doctype": "WAFD Document Template", "name": stable, "template_title": title,
                "reference_doctype": doctype, "document_category": category, "enabled": 1,
                "is_default": 1 if category in {"Hotel Undertaking", "Contract", "Invoice"} else 0,
            })
            doc.flags.name_set = True
            doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
    templates = frappe.get_all("WAFD Document Template", filters={"enabled": 1}, fields=["name", "document_category"])
    for row in templates:
        if row.document_category not in mapping:
            continue
        doc = frappe.get_doc("WAFD Document Template", row.name)
        doc.logo = LOGO
        doc.page_size = "A4"
        doc.orientation = "Portrait"
        doc.direction = "RTL"
        doc.margin_top_mm = 0
        doc.margin_right_mm = 0
        doc.margin_bottom_mm = 0
        doc.margin_left_mm = 0
        doc.canvas_json = json.dumps(mapping[row.document_category], ensure_ascii=False)
        doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype="WAFD Document Template")
