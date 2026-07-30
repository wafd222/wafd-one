import json
import frappe

from wafd_one.patches.v10_0_0_rc36.execute import generic_operational, invoice_canvas, LOGO

TAX_NUMBER = "314262038700003"
WEBSITE = "www.wafdalmadinah.com"


def _save_template(reference_doctype, title, category, canvas, is_default=1):
    # Keep patch migrations compatible with the Select options defined on
    # WAFD Document Template. Older aliases are normalized here so a typo or
    # legacy value can never stop bench migrate.
    category_aliases = {
        "Undertaking": "Hotel Undertaking",
        "Loading": "Loading Order",
        "Delivery": "Delivery Note",
    }
    category = category_aliases.get(category, category)

    allowed_categories = {
        "Hotel Undertaking",
        "Contract",
        "Quotation",
        "Invoice",
        "Operation Order",
        "Production Order",
        "Preparation Order",
        "Loading Order",
        "Delivery Note",
        "Certificate",
        "Report",
        "Other",
    }
    if category not in allowed_categories:
        category = "Other"
    name = frappe.db.get_value(
        "WAFD Document Template",
        {"reference_doctype": reference_doctype, "enabled": 1, "is_default": 1},
        "name",
    ) or frappe.db.get_value(
        "WAFD Document Template",
        {"reference_doctype": reference_doctype, "enabled": 1},
        "name",
    )
    if name:
        doc = frappe.get_doc("WAFD Document Template", name)
    else:
        doc = frappe.get_doc({
            "doctype": "WAFD Document Template",
            "template_title": title,
            "reference_doctype": reference_doctype,
            "document_category": category,
            "enabled": 1,
            "is_default": is_default,
        })
    doc.template_title = title
    doc.reference_doctype = reference_doctype
    doc.document_category = category
    doc.enabled = 1
    doc.is_default = is_default
    doc.logo = LOGO
    doc.page_size = "A4"
    doc.orientation = "Portrait"
    doc.direction = "RTL"
    doc.margin_top_mm = 0
    doc.margin_right_mm = 0
    doc.margin_bottom_mm = 0
    doc.margin_left_mm = 0
    doc.canvas_json = json.dumps(canvas, ensure_ascii=False)
    doc.custom_css = """
html, body { width:100%; height:100%; }
table, tr, td, th { page-break-inside: avoid !important; }
.wds-print-page { page-break-after: avoid !important; page-break-inside: avoid !important; }
"""
    doc.save(ignore_permissions=True)


def _invoice_with_tax_identity():
    canvas = invoice_canvas()
    for block in canvas.get("blocks", []):
        html = block.get("html") or ""
        html = html.replace("wafd.almadinah@gmail.com", WEBSITE)
        if block.get("id") == "brand" and TAX_NUMBER not in html:
            html = html.replace(
                "</div></div>",
                f'<div style="font-size:10px;color:#555;margin-top:4px;direction:rtl;">الرقم الضريبي: <span dir="ltr">{TAX_NUMBER}</span> &nbsp; | &nbsp; الموقع: <span dir="ltr">{WEBSITE}</span></div></div></div>',
                1,
            )
        if block.get("id") == "footer":
            html = html.replace(
                f'<span dir="ltr">0500336989 &nbsp; | &nbsp; {WEBSITE}</span>',
                f'<span dir="ltr">0500336989 &nbsp; | &nbsp; {WEBSITE} &nbsp; | &nbsp; VAT: {TAX_NUMBER}</span>',
            )
        block["html"] = html
    return canvas


def _packaging_canvas():
    return generic_operational("أمر تغليف", "PACKAGING ORDER", [
        [("المشروع / Project", '{{ doc.project or "" }}'), ("دفعة الإنتاج / Production Batch", '{{ doc.production_batch or "" }}')],
        [("خطة الوجبة / Meal Plan", '{{ doc.meal_plan or "" }}'), ("تاريخ التغليف / Packaging Date", '{{ frappe.utils.formatdate(doc.packaging_date) if doc.packaging_date else "" }}')],
        [("الكمية المخططة / Planned Qty", '{{ doc.planned_quantity or 0 }}'), ("الكمية المغلفة / Packed Qty", '{{ doc.packed_quantity or 0 }}')],
        [("عدد الصناديق / Boxes", '{{ doc.box_count or 0 }}'), ("الوحدات بالصندوق / Units per Box", '{{ doc.units_per_box or 0 }}')],
        [("عدد سخانات الهوت كابن / Hot Cabinets", '{{ doc.hot_cabinet_count or 0 }}'), ("إجمالي السفندشات / Sandwich Total", '{{ doc.hot_cabinet_sandwich_total or 0 }}')],
        [("المشرف / Supervisor", '{{ doc.supervisor or "" }}'), ("الحالة / Status", '{{ doc.status or "" }}')],
    ], '<div style="direction:rtl;border:1px solid #ddd;padding:12px;font-size:11px;line-height:1.8;"><b>بيان التغليف / Packaging Manifest</b><br><pre style="white-space:pre-wrap;font-family:Arial;">{{ doc.box_manifest or "لا يوجد بيان صناديق" }}</pre><br><b>ملاحظات / Notes:</b> {{ doc.notes or "" }}</div>')


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    _save_template("WAFD Invoice", "الفاتورة الضريبية الاحترافية", "Invoice", _invoice_with_tax_identity())
    if frappe.db.exists("DocType", "WAFD Packaging Record"):
        _save_template("WAFD Packaging Record", "أمر التغليف", "Other", _packaging_canvas())
    frappe.clear_cache(doctype="WAFD Document Template")
