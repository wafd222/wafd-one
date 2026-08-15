from __future__ import annotations

import json

import frappe

from wafd_one.finance import refresh_project_financials
from wafd_one.patches.v10_0_0_rc36.execute import LOGO, b


WEBSITE = "www.wafdalmadinah.com"
PHONE = "0500336989"


def _certificate_canvas():
    body = (
        '<div style="direction:rtl;text-align:right;font-size:15px;line-height:2.15;color:#222;">'
        'تشهد الجهة المستفيدة <b>{{ doc.mission or "الجهة المستفيدة" }}</b> بأن '
        '<b>شركة وفد المدينة لخدمات الإعاشة</b> قد أتمت تقديم خدمات الإعاشة '
        'للمشروع رقم <b><span dir="ltr">{{ doc.name or "" }}</span></b> '
        'في فندق <b>{{ doc.primary_hotel or "................" }}</b> خلال الفترة من '
        '<b>{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }}</b> إلى '
        '<b>{{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}</b>، '
        'وتم استلام الخدمات وفق الكميات والمواصفات المتفق عليها.'
        '</div>'
    )
    info = (
        '<table style="width:100%;table-layout:fixed;border-collapse:collapse;direction:rtl;font-size:11px;">'
        '<tr>'
        '<td style="border:1px solid #d6d6d6;padding:8px;"><b>رقم المشروع / Project No.</b><br><span dir="ltr">{{ doc.name or "" }}</span></td>'
        '<td style="border:1px solid #d6d6d6;padding:8px;"><b>الفندق / Hotel</b><br>{{ doc.primary_hotel or "" }}</td>'
        '</tr><tr>'
        '<td style="border:1px solid #d6d6d6;padding:8px;"><b>الفترة / Period</b><br>{{ frappe.utils.formatdate(doc.start_date) if doc.start_date else "" }} — {{ frappe.utils.formatdate(doc.end_date) if doc.end_date else "" }}</td>'
        '<td style="border:1px solid #d6d6d6;padding:8px;"><b>الوجبات / Meals</b><br>المخطط {{ doc.total_meals or 0 }} &nbsp; | &nbsp; المسلم {{ doc.delivered_meals or 0 }}</td>'
        '</tr>'
        '</table>'
    )
    signature = (
        '<table style="width:100%;table-layout:fixed;direction:rtl;text-align:center;font-size:12px;line-height:1.9;">'
        '<tr><td>اسم ممثل الجهة المستفيدة<br><br>____________________</td>'
        '<td>التوقيع والختم<br><br>____________________</td>'
        '<td>التاريخ<br><br>____________________</td></tr></table>'
    )
    blocks = [
        b("logo", "logo", 675, 24, 70, 64, src=LOGO, z=20),
        b("brand", "text", 48, 28, 610, 62,
          '<div style="direction:rtl;border-bottom:2px solid #b88a2a;padding:2px 0 10px;">'
          '<div style="font-size:20px;font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>'
          '<div style="font-size:10px;color:#666;letter-spacing:.25px;">WAFD AL-MADINAH CATERING SERVICES</div></div>'),
        b("title", "text", 48, 112, 697, 60,
          '<div style="text-align:center;font-size:24px;font-weight:700;">شهادة استلام وشكر</div>'
          '<div style="text-align:center;font-size:11px;color:#666;">SERVICE ACCEPTANCE & APPRECIATION CERTIFICATE</div>'),
        b("body", "text", 70, 215, 655, 250, body, font_size=15),
        b("info", "text", 70, 500, 655, 150, info, font_size=11),
        b("signature", "text", 70, 735, 655, 150, signature, font_size=12),
        b("footer", "text", 48, 1000, 697, 48,
          '<div style="border-top:1px solid #b88a2a;padding-top:7px;text-align:center;font-size:9px;color:#666;line-height:1.6;direction:rtl;">'
          'شركة وفد المدينة لخدمات الإعاشة — المدينة المنورة &nbsp; | &nbsp; '
          f'<span dir="ltr">{PHONE} &nbsp; | &nbsp; {WEBSITE}</span></div>'),
    ]
    return {"version": 4, "blocks": blocks}


def _ensure_service_certificate_template():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return None

    rows = frappe.get_all(
        "WAFD Document Template",
        filters={"reference_doctype": "WAFD Catering Project"},
        fields=["name", "template_title", "is_default", "enabled"],
        order_by="is_default desc, modified desc",
    )
    clean = next(
        (
            row for row in rows
            if (row.template_title or "").strip() == "شهادة استلام وشكر"
            and "OPERATION" not in (row.name or "").upper()
        ),
        None,
    )

    # A legacy database may have reused a technical OPERATION-ORDER identifier
    # for the certificate. Keep that historical row for compatibility, but make
    # a clean certificate record the project default so Preview/PDF no longer
    # expose a misleading operation-order template identity.
    if clean:
        doc = frappe.get_doc("WAFD Document Template", clean.name)
    else:
        frappe.db.set_value(
            "WAFD Document Template",
            {"reference_doctype": "WAFD Catering Project", "is_default": 1},
            "is_default", 0, update_modified=False,
        )
        doc = frappe.get_doc({
            "doctype": "WAFD Document Template",
            "template_title": "شهادة استلام وشكر",
            "reference_doctype": "WAFD Catering Project",
            "document_category": "Certificate",
            "enabled": 1,
            "is_default": 1,
            "page_size": "A4",
            "orientation": "Portrait",
            "direction": "RTL",
            "margin_top_mm": 0,
            "margin_right_mm": 0,
            "margin_bottom_mm": 0,
            "margin_left_mm": 0,
            "logo": LOGO,
            "canvas_json": json.dumps(_certificate_canvas(), ensure_ascii=False),
        })
        doc.insert(ignore_permissions=True)

    doc.template_title = "شهادة استلام وشكر"
    doc.reference_doctype = "WAFD Catering Project"
    doc.document_category = "Certificate"
    doc.enabled = 1
    doc.is_default = 1
    doc.page_size = "A4"
    doc.orientation = "Portrait"
    doc.direction = "RTL"
    doc.margin_top_mm = 0
    doc.margin_right_mm = 0
    doc.margin_bottom_mm = 0
    doc.margin_left_mm = 0
    doc.logo = LOGO
    doc.canvas_json = json.dumps(_certificate_canvas(), ensure_ascii=False)
    doc.custom_css = (
        "html,body{width:100%;height:100%;}"
        "table,tr,td,th{page-break-inside:avoid!important;}"
        ".wds-print-page{page-break-after:avoid!important;page-break-inside:avoid!important;}"
    )
    doc.save(ignore_permissions=True)
    return doc.name


def execute():
    # Schema first: RC146 adds explicit collected-gross and collected-VAT fields.
    if frappe.db.exists("DocType", "WAFD Catering Project"):
        frappe.reload_doc("wafd_one", "doctype", "wafd_catering_project", force=True)

    # Re-run the RC145 repair because it is idempotent and ensures older projects
    # reach the furthest persisted operational stage before finance is refreshed.
    try:
        from wafd_one.patches.v10_0_0_rc145.execute import execute as sync_workflow_states
        sync_workflow_states()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "RC146 workflow-state refresh")

    if frappe.db.exists("DocType", "WAFD Catering Project"):
        for project_name in frappe.get_all("WAFD Catering Project", pluck="name"):
            try:
                refresh_project_financials(project_name)
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"RC146 project finance refresh: {project_name}")

    try:
        _ensure_service_certificate_template()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "RC146 service certificate refresh")

    frappe.clear_cache()
