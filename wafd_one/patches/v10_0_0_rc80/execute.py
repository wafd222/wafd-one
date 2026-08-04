import json
import frappe
from wafd_one.document_studio import compile_template


def _block(block_id, block_type, x, y, w, h, html="", **kwargs):
    data = {"id": block_id, "type": block_type, "x": x, "y": y, "w": w, "h": h,
            "z": kwargs.pop("z", 1), "html": html, "font_family": "Arial",
            "font_size": kwargs.pop("font_size", 12), "color": kwargs.pop("color", "#111111"),
            "background": kwargs.pop("background", "transparent"), "opacity": 1, "rotation": 0}
    data.update(kwargs)
    return data


def undertaking_canvas():
    logo = "/assets/wafd_one/images/wafd-almadinah-official.png"
    blocks = [
        _block("logo", "logo", 675, 24, 70, 64, src='{{ doc.company_logo or "' + logo + '" }}', z=20),
        _block("brand", "text", 48, 28, 610, 62, '<div style="direction:rtl;border-bottom:2px solid #b88a2a;padding:2px 0 10px;"><div style="font-size:20px;font-weight:700;">{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }}</div><div style="font-size:10px;color:#666;">WAFD AL-MADINAH CATERING SERVICES</div></div>'),
        _block("title", "text", 48, 104, 697, 54, '<div style="text-align:center;font-size:24px;font-weight:700;">تعهد تقديم خدمات الإعاشة</div><div style="text-align:center;font-size:11px;color:#666;">CATERING SERVICES UNDERTAKING</div>'),
        _block("docno", "field", 48, 166, 697, 34, '<div style="direction:rtl;font-size:10px;color:#666;text-align:left;">رقم التعهد: <span dir="ltr">{{ doc.name or "" }}</span></div>'),
        _block("body", "field", 58, 210, 677, 155, '<div style="direction:rtl;text-align:justify;font-size:13px;line-height:2.05;"><p>نحن <b>{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }}</b>، سجل تجاري رقم <b>{{ doc.company_cr or "7051832694" }}</b>، نتعهد بتقديم خدمات الإعاشة للمستفيدين في فندق <b>{{ doc.hotel or "................" }}</b> وفق البيانات الموضحة أدناه، وبالالتزام بالاشتراطات الصحية والتنظيمية وجودة وسلامة الوجبات أثناء التجهيز والنقل والتسليم.</p><p>ويصدر هذا التعهد من طرف واحد من شركة وفد المدينة لخدمات الإعاشة ويُعتمد بتوقيع المدير العام وختم الشركة.</p></div>'),
        _block("details", "field", 48, 380, 697, 260, '<table style="width:100%;table-layout:fixed;border-collapse:collapse;direction:rtl;font-size:11px;"><tr><td style="border:1px solid #d5d5d5;padding:7px;"><b>التاريخ</b><br>{{ frappe.utils.formatdate(doc.undertaking_date) if doc.undertaking_date else "" }}</td><td style="border:1px solid #d5d5d5;padding:7px;"><b>الفندق</b><br>{{ doc.hotel or "" }}</td></tr><tr><td style="border:1px solid #d5d5d5;padding:7px;"><b>البعثة أو العميل</b><br>{{ doc.mission or doc.second_party_name or "" }}</td><td style="border:1px solid #d5d5d5;padding:7px;"><b>عدد المستفيدين</b><br>{{ doc.beneficiary_count or 0 }}</td></tr><tr><td style="border:1px solid #d5d5d5;padding:7px;"><b>الجنسية</b><br>{{ doc.nationality or "" }}</td><td style="border:1px solid #d5d5d5;padding:7px;"><b>مدة الخدمة</b><br>{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}</td></tr><tr><td style="border:1px solid #d5d5d5;padding:7px;"><b>الوجبات</b><br>{{ doc.meal_types or "" }}</td><td style="border:1px solid #d5d5d5;padding:7px;"><b>موقع التوريد</b><br>{{ doc.supply_location or "" }}</td></tr></table>'),
        _block("terms", "field", 48, 655, 697, 100, '<div style="direction:rtl;border:1px solid #ddd;padding:10px;font-size:11px;line-height:1.75;"><b>بنود وملاحظات إضافية</b><br>{{ doc.additional_terms or doc.service_notes or "لا يوجد" }}</div>'),
        _block("approval_text", "field", 430, 775, 285, 105, '<div style="direction:rtl;text-align:center;font-size:12px;line-height:1.8;"><b>شركة وفد المدينة لخدمات الإعاشة</b><br><b>{{ doc.signatory_title or "المدير العام" }}</b><div style="position:relative;height:56px;margin-top:2px;"><div style="position:absolute;left:0;right:0;bottom:2px;font-weight:700;z-index:2;">{{ doc.authorized_signatory or doc.company_representative or "نزار بن مذير بن ظفر" }}</div></div></div>'),
        _block("stamp", "stamp", 485, 805, 170, 140, src='{{ doc.company_stamp or "" }}', z=8),
        _block("signature", "signature", 475, 840, 190, 82, src='{{ doc.signature_image or "" }}', z=12),
        _block("footer", "text", 48, 974, 697, 48, '<div style="border-top:1px solid #b88a2a;padding-top:7px;text-align:center;font-size:9px;color:#666;line-height:1.6;direction:rtl;">{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }} — {{ doc.company_address or "حي الملك فهد، المدينة المنورة" }} &nbsp; | &nbsp; <span dir="ltr">{{ doc.company_phone or "0500336989" }} &nbsp; | &nbsp; {{ doc.company_email or "wafd.almadinah@gmail.com" }}</span></div>'),
    ]
    return {"version": 4, "blocks": blocks}


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_print_settings")
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking")
    if frappe.db.exists("DocType", "WAFD Print Settings"):
        settings = frappe.get_single("WAFD Print Settings")
        defaults = {"company_name":"شركة وفد المدينة لخدمات الإعاشة","company_cr":"7051832694","company_address":"حي الملك فهد، المدينة المنورة","company_phone":"0500336989","company_email":"wafd.almadinah@gmail.com","signatory_name":"نزار بن مذير بن ظفر","signatory_title":"المدير العام"}
        for key,value in defaults.items():
            if not settings.get(key) or key == "signatory_name": settings.set(key,value)
        settings.save(ignore_permissions=True)
    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        values={"company_representative":"نزار بن مذير بن ظفر","authorized_signatory":"نزار بن مذير بن ظفر"}
        for name in frappe.get_all("WAFD Hotel Undertaking", pluck="name"):
            frappe.db.set_value("WAFD Hotel Undertaking", name, values, update_modified=False)
    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()
    if frappe.db.exists("DocType", "WAFD Document Template"):
        canvas=json.dumps(undertaking_canvas(),ensure_ascii=False)
        for name in frappe.get_all("WAFD Document Template", filters={"document_category":"Hotel Undertaking"}, pluck="name"):
            doc=frappe.get_doc("WAFD Document Template",name)
            doc.page_size="A4"; doc.orientation="Portrait"; doc.direction="RTL"
            doc.margin_top_mm=doc.margin_right_mm=doc.margin_bottom_mm=doc.margin_left_mm=0
            doc.canvas_json=canvas; doc.compiled_html=compile_template(doc); doc.enabled=1; doc.is_default=1
            doc.save(ignore_permissions=True)
    frappe.clear_cache()
