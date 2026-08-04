import json
from pathlib import Path

import frappe

from wafd_one.document_studio import compile_template


LOGO = "/assets/wafd_one/images/wafd-almadinah-official.png"


def _block(block_id, block_type, x, y, w, h, html="", **kwargs):
    data = {
        "id": block_id,
        "type": block_type,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "z": kwargs.pop("z", 1),
        "html": html,
        "font_family": "Arial",
        "font_size": kwargs.pop("font_size", 12),
        "color": kwargs.pop("color", "#111111"),
        "background": kwargs.pop("background", "transparent"),
        "opacity": kwargs.pop("opacity", 1),
        "rotation": kwargs.pop("rotation", 0),
    }
    data.update(kwargs)
    return data


def undertaking_canvas():
    """Restore the approved undertaking layout and change only its approval area."""
    header = (
        '<div style="direction:rtl;border-bottom:1px solid #b88a2a;padding:0 0 9px;">'
        '<div style="font-size:20px;font-weight:700;line-height:1.35;">شركة وفد المدينة لخدمات الإعاشة</div>'
        '<div style="font-size:10px;color:#777;letter-spacing:.15px;">WAFD AL-MADINAH CATERING SERVICES</div>'
        '</div>'
    )
    intro = (
        '<div style="direction:rtl;text-align:justify;font-size:12.5px;line-height:1.85;">'
        '<p style="margin:0 0 8px;">نحن <b>{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }}</b>، '
        'سجل تجاري رقم <b>{{ doc.company_cr or "7051832694" }}</b>، نتعهد بتقديم خدمات الإعاشة للمستفيدين '
        'في فندق <b>{{ doc.hotel or "................" }}</b> وفق البيانات الموضحة أدناه، وبالالتزام بالاشتراطات '
        'الصحية والتنظيمية المعمول بها، وجودة وسلامة الوجبات أثناء التجهيز والنقل والتسليم.</p>'
        '<p style="margin:0;">ويصدر هذا التعهد من طرف واحد من شركة وفد المدينة لخدمات الإعاشة، '
        'ويُعتمد بتوقيع المدير العام وختم الشركة.</p></div>'
    )
    details = (
        '<table style="width:100%;table-layout:fixed;border-collapse:collapse;direction:rtl;font-size:10.5px;line-height:1.55;">'
        '<tr><td style="border:1px solid #d6d6d6;padding:6px;"><b>التاريخ / Date</b><br>{{ frappe.utils.formatdate(doc.undertaking_date) if doc.undertaking_date else "" }}</td>'
        '<td style="border:1px solid #d6d6d6;padding:6px;"><b>المشروع / Project</b><br>{{ doc.project or "" }}</td></tr>'
        '<tr><td style="border:1px solid #d6d6d6;padding:6px;"><b>الفندق / Hotel</b><br>{{ doc.hotel or "" }}</td>'
        '<td style="border:1px solid #d6d6d6;padding:6px;"><b>البعثة أو العميل / Mission or Client</b><br>{{ doc.mission or doc.second_party_name or "" }}</td></tr>'
        '<tr><td style="border:1px solid #d6d6d6;padding:6px;"><b>عدد المستفيدين / Beneficiaries</b><br>{{ doc.beneficiary_count or 0 }}</td>'
        '<td style="border:1px solid #d6d6d6;padding:6px;"><b>الجنسية / Nationality</b><br>{{ doc.nationality or "" }}</td></tr>'
        '<tr><td style="border:1px solid #d6d6d6;padding:6px;"><b>مدة الخدمة / Service Period</b><br>{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}</td>'
        '<td style="border:1px solid #d6d6d6;padding:6px;"><b>موقع التوريد / Supply Location</b><br>{{ doc.supply_location or doc.hotel or "" }}</td></tr>'
        '<tr><td colspan="2" style="border:1px solid #d6d6d6;padding:6px;"><b>الوجبات / Meals</b><br>{{ doc.meal_types or "" }}</td></tr>'
        '</table>'
    )
    terms = (
        '<div style="direction:rtl;border:1px solid #d6d6d6;padding:8px;font-size:10.5px;line-height:1.55;">'
        '<b>بنود وملاحظات إضافية / Additional Terms</b><br>'
        '{{ doc.additional_terms or doc.service_notes or "لا يوجد" }}'
        '</div>'
    )
    signatory = (
        '<div style="direction:rtl;text-align:center;font-size:11px;line-height:1.5;">'
        '<div style="font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>'
        '<div style="font-weight:700;margin-top:2px;">المدير العام</div>'
        '<div style="position:relative;height:72px;margin-top:0;">'
        '<div style="position:absolute;left:0;right:0;bottom:3px;font-weight:700;font-size:12px;z-index:2;">'
        '{{ doc.authorized_signatory or doc.company_representative or "نزار بن مذير بن ظفر" }}'
        '</div></div></div>'
    )
    footer = (
        '<div style="border-top:1px solid #b88a2a;padding-top:7px;text-align:center;font-size:9px;color:#666;line-height:1.5;direction:rtl;">'
        '{{ doc.company_name or "شركة وفد المدينة لخدمات الإعاشة" }} — {{ doc.company_address or "المدينة المنورة — حي الملك فهد" }}'
        ' &nbsp; | &nbsp; <span dir="ltr">{{ doc.company_phone or "0500336989" }} &nbsp; | &nbsp; '
        '{{ doc.company_email or "wafd.almadinah@gmail.com" }}</span></div>'
    )

    return {
        "version": 5,
        "blocks": [
            _block("logo", "logo", 675, 26, 70, 64, src="{{ doc.company_logo or '/assets/wafd_one/images/wafd-almadinah-official.png' }}", z=20),
            _block("brand", "text", 48, 30, 610, 62, header),
            _block("title", "text", 48, 108, 697, 50,
                   '<div style="text-align:center;direction:rtl;font-size:23px;font-weight:700;">تعهد تقديم خدمات الإعاشة</div>'
                   '<div style="text-align:center;font-size:10px;color:#777;">CATERING SERVICES UNDERTAKING</div>'),
            _block("docno", "field", 48, 164, 697, 30,
                   '<div style="direction:rtl;font-size:10px;color:#666;text-align:left;">رقم التعهد / Undertaking No.: '
                   '<span dir="ltr">{{ doc.name or "" }}</span></div>'),
            _block("body", "field", 58, 202, 677, 150, intro),
            _block("details", "field", 48, 365, 697, 270, details),
            _block("terms", "field", 48, 648, 697, 78, terms),
            _block("signatory", "field", 190, 744, 430, 145, signatory, z=2),
            # Stamp is larger and placed directly below "المدير العام".
            _block("stamp", "stamp", 408, 787, 165, 122,
                   src='{{ doc.company_stamp or "" }}', z=3),
            # Signature overlays the middle of the manager name, exactly as requested.
            _block("signature", "signature", 272, 830, 235, 72,
                   src='{{ doc.signature_image or "" }}', z=5),
            _block("footer", "text", 48, 946, 697, 48, footer),
        ],
    }


def _install_document_studio_template():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return

    names = frappe.get_all(
        "WAFD Document Template",
        filters={"reference_doctype": "WAFD Hotel Undertaking"},
        pluck="name",
    )
    canvas = undertaking_canvas()
    for name in names:
        doc = frappe.get_doc("WAFD Document Template", name)
        # Do not touch templates for invoices, loading, delivery, or any other document.
        if doc.reference_doctype != "WAFD Hotel Undertaking":
            continue
        doc.logo = LOGO
        doc.page_size = "A4"
        doc.orientation = "Portrait"
        doc.direction = "RTL"
        doc.margin_top_mm = 0
        doc.margin_right_mm = 0
        doc.margin_bottom_mm = 0
        doc.margin_left_mm = 0
        doc.canvas_json = json.dumps(canvas, ensure_ascii=False)
        # Undertaking-only override: prevents wkhtmltopdf from creating a second page.
        doc.custom_css = (
            ".wds-print-page{height:995px!important;max-height:995px!important;"
            "min-height:995px!important;overflow:hidden!important;page-break-after:avoid!important;}"
            "html,body{height:995px!important;max-height:995px!important;overflow:hidden!important;}"
        )
        doc.compiled_html = compile_template(doc)
        doc.enabled = 1
        doc.is_default = 1
        doc.save(ignore_permissions=True)

    frappe.clear_cache(doctype="WAFD Document Template")


def _install_print_format_fallback():
    """Update only the hotel undertaking Print Format fallback."""
    source = (
        Path(__file__).resolve().parents[2]
        / "wafd_one" / "print_format" / "wafd_hotel_undertaking"
        / "wafd_hotel_undertaking.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    html = data.get("html") or ""
    for name in frappe.get_all(
        "Print Format",
        filters={"doc_type": "WAFD Hotel Undertaking"},
        pluck="name",
    ):
        frappe.db.set_value(
            "Print Format",
            name,
            {
                "html": html,
                "custom_format": 1,
                "print_format_type": "Jinja",
                "disabled": 0,
                "raw_printing": 0,
            },
            update_modified=False,
        )
    frappe.clear_cache(doctype="Print Format")


def execute():
    _install_document_studio_template()
    _install_print_format_fallback()
