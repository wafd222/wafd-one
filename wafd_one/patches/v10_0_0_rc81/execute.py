import json
import frappe

LOGO = "/assets/wafd_one/images/wafd-almadinah-official.png"


def b(block_id, block_type, x, y, w, h, html="", **kwargs):
    data = {
        "id": block_id, "type": block_type, "x": x, "y": y, "w": w, "h": h,
        "z": kwargs.pop("z", 1), "html": html, "font_family": "Arial",
        "font_size": kwargs.pop("font_size", 12), "color": kwargs.pop("color", "#111111"),
        "background": kwargs.pop("background", "transparent"), "opacity": 1, "rotation": 0,
    }
    data.update(kwargs)
    return data


def info_table(rows):
    html = ['<table style="width:100%;table-layout:fixed;border-collapse:collapse;direction:rtl;font-size:11px;">']
    for row in rows:
        html.append('<tr>')
        for label, value in row:
            html.append(f'<td style="border:1px solid #d5d5d5;padding:7px;vertical-align:top;"><b>{label}</b><br>{value}</td>')
        html.append('</tr>')
    html.append('</table>')
    return ''.join(html)


def undertaking_canvas():
    body = ('<div style="direction:rtl;text-align:justify;font-size:13px;line-height:2.05;">'
        '<p>نحن <b>{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }}</b>، سجل تجاري رقم <b>{{ doc.company_cr or "7051832694" }}</b>، '
        'نتعهد بتقديم خدمات الإعاشة للمستفيدين في فندق <b>{{ doc.hotel or "................" }}</b> وفق البيانات الموضحة أدناه، '
        'وبالالتزام بالاشتراطات الصحية والتنظيمية المعمول بها، وجودة وسلامة الوجبات أثناء التجهيز والنقل والتسليم.</p>'
        '<p>ويصدر هذا التعهد من طرف واحد من شركة وفد المدينة لخدمات الإعاشة، ويُعتمد بتوقيع ممثل الشركة وختمها.</p></div>')
    details = info_table([
        [("التاريخ / Date", '{{ frappe.utils.formatdate(doc.undertaking_date) if doc.undertaking_date else "" }}'),
         ("المشروع / Project", '{{ doc.project or "" }}')],
        [("البعثة أو العميل / Mission or Client", '{{ doc.mission or doc.second_party_name or "" }}'),
         ("الفندق / Hotel", '{{ doc.hotel or "" }}')],
        [("عدد المستفيدين / Beneficiaries", '{{ doc.beneficiary_count or 0 }}'),
         ("الجنسية / Nationality", '{{ doc.nationality or "" }}')],
        [("مدة الخدمة / Service Period", '{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}'),
         ("موقع التوريد / Supply Location", '{{ doc.supply_location or "" }}')],
        [("الوجبات / Meals", '{{ doc.meal_types or "" }}'),
         ("الحالة / Status", '{{ doc.status or "" }}')],
    ])
    blocks = [
        b("logo", "logo", 675, 24, 70, 64, src=LOGO, z=20),
        b("brand", "text", 48, 28, 610, 62,
          '<div style="direction:rtl;border-bottom:2px solid #b88a2a;padding:2px 0 10px;">'
          '<div style="font-size:20px;font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>'
          '<div style="font-size:10px;color:#666;letter-spacing:.25px;">WAFD AL-MADINAH CATERING SERVICES</div></div>'),
        b("title", "text", 48, 104, 697, 54,
          '<div style="text-align:center;font-size:24px;font-weight:700;">تعهد تقديم خدمات الإعاشة</div>'
          '<div style="text-align:center;font-size:11px;color:#666;">CATERING SERVICES UNDERTAKING</div>'),
        b("docno", "field", 48, 166, 697, 36, '<div style="direction:rtl;font-size:10px;color:#666;text-align:left;">رقم التعهد / Undertaking No.: <span dir="ltr">{{ doc.name or "" }}</span></div>'),
        b("body", "field", 58, 214, 677, 210, body),
        b("details", "field", 48, 440, 697, 270, details),
        b("terms", "field", 48, 726, 697, 92, '<div style="direction:rtl;border:1px solid #ddd;padding:10px;font-size:11px;line-height:1.75;"><b>بنود وملاحظات إضافية / Additional Terms</b><br>{{ doc.additional_terms or doc.service_notes or "لا يوجد" }}</div>'),
        b("company", "field", 48, 830, 310, 30, '<div style="direction:rtl;text-align:center;font-size:12px;font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>', z=4),
        b("signatory_name", "field", 48, 867, 310, 36, '<div style="direction:rtl;text-align:center;font-size:12px;font-weight:700;">{{ doc.authorized_signatory or doc.company_representative or "نزار بن مذير بن ظفر" }}</div>', z=5),
        # Signature intentionally overlaps the middle of the printed name.
        b("signature", "signature", 82, 842, 242, 78, src='{{ doc.signature_image or "" }}', z=15),
        b("signatory_title", "field", 48, 905, 310, 34, '<div style="direction:rtl;text-align:center;font-size:11px;">{{ doc.signatory_title or "المدير العام / General Manager" }}</div>', z=5),
        # Large stamp directly below the General Manager title.
        b("stamp", "stamp", 88, 928, 230, 78, src='{{ doc.company_stamp or "" }}', z=12),
        b("footer", "text", 48, 1008, 697, 30,
          '<div style="border-top:1px solid #b88a2a;padding-top:5px;text-align:center;font-size:8.5px;color:#666;direction:rtl;">'
          'شركة وفد المدينة لخدمات الإعاشة — المدينة المنورة &nbsp; | &nbsp; '
          '<span dir="ltr">0500336989 | wafd.almadinah@gmail.com</span></div>'),
    ]
    return {"version": 5, "blocks": blocks}


def execute():
    if frappe.db.exists("DocType", "WAFD Print Settings"):
        settings = frappe.get_single("WAFD Print Settings")
        if settings.meta.has_field("default_company_name") and not settings.default_company_name:
            settings.default_company_name = "شركة وفد المدينة لخدمات الإعاشة"
        if settings.meta.has_field("default_company_cr") and not settings.default_company_cr:
            settings.default_company_cr = "7051832694"
        if settings.meta.has_field("default_company_representative") and not settings.default_company_representative:
            settings.default_company_representative = "نزار بن مذير بن ظفر"
        if settings.meta.has_field("default_company_phone") and not settings.default_company_phone:
            settings.default_company_phone = "0500336989"
        if settings.meta.has_field("default_company_email") and not settings.default_company_email:
            settings.default_company_email = "wafd.almadinah@gmail.com"
        if settings.signatory_name in (None, "", "نزار نذير بن ظفر"):
            settings.signatory_name = "نزار بن مذير بن ظفر"
        settings.flags.ignore_permissions = True
        settings.save()

    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        if frappe.db.has_column("WAFD Hotel Undertaking", "use_saved_company_data"):
            frappe.db.sql("""update `tabWAFD Hotel Undertaking`
                set use_saved_company_data=1
                where use_saved_company_data is null""")

    if frappe.db.exists("DocType", "WAFD Document Template"):
        names = frappe.get_all(
            "WAFD Document Template",
            filters={"reference_doctype": "WAFD Hotel Undertaking"},
            pluck="name",
        )
        canvas = json.dumps(undertaking_canvas(), ensure_ascii=False)
        for name in names:
            doc = frappe.get_doc("WAFD Document Template", name)
            doc.logo = LOGO
            doc.page_size = "A4"
            doc.orientation = "Portrait"
            doc.direction = "RTL"
            doc.margin_top_mm = 0
            doc.margin_right_mm = 0
            doc.margin_bottom_mm = 0
            doc.margin_left_mm = 0
            doc.canvas_json = canvas
            doc.compiled_html = ""
            doc.save(ignore_permissions=True)
        frappe.clear_cache(doctype="WAFD Document Template")

    frappe.clear_cache(doctype="WAFD Hotel Undertaking")
    frappe.clear_cache(doctype="WAFD Print Settings")
