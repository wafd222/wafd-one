import json

import frappe

LOGO = "/assets/wafd_one/images/wafd-almadinah-official.png"


def _block(block_id, block_type, x, y, w, h, html="", **kwargs):
    value = {
        "id": block_id,
        "type": block_type,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "z": kwargs.pop("z", 1),
        "html": html,
        "font_family": "Arial",
        "font_size": kwargs.pop("font_size", 13),
        "color": kwargs.pop("color", "#111111"),
        "background": kwargs.pop("background", "transparent"),
        "opacity": 1,
        "rotation": 0,
    }
    value.update(kwargs)
    return value


def _invoice_canvas():
    return {
        "version": 3,
        "blocks": [
            _block("logo", "logo", 650, 22, 92, 76, src=LOGO, z=3),
            _block(
                "brand", "text", 48, 30, 580, 66,
                '<div style="direction:rtl;border-bottom:3px solid #b88a2a;padding:4px 0 12px;">'
                '<div style="font-size:22px;font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>'
                '<div style="font-size:11px;color:#555;margin-top:4px;letter-spacing:.3px;">WAFD AL-MADINAH CATERING SERVICES</div>'
                '</div>',
            ),
            _block(
                "title", "text", 48, 112, 694, 52,
                '<div style="text-align:center;font-size:26px;font-weight:700;">فاتورة ضريبية</div>'
                '<div style="text-align:center;font-size:13px;color:#666;">TAX INVOICE</div>',
            ),
            _block(
                "meta", "field", 48, 176, 694, 104,
                '<table style="width:100%;table-layout:fixed;font-size:12px;border-collapse:collapse;direction:rtl;">'
                '<tr>'
                '<td style="padding:8px;border:1px solid #ccc;"><b>رقم الفاتورة</b><br><span dir="ltr">{{ doc.name or "" }}</span><br><small>Invoice No.</small></td>'
                '<td style="padding:8px;border:1px solid #ccc;"><b>تاريخ الفاتورة</b><br>{{ frappe.utils.formatdate(doc.invoice_date) if doc.invoice_date else "" }}<br><small>Invoice Date</small></td>'
                '<td style="padding:8px;border:1px solid #ccc;"><b>تاريخ الاستحقاق</b><br>{{ frappe.utils.formatdate(doc.due_date) if doc.due_date else "" }}<br><small>Due Date</small></td>'
                '</tr><tr>'
                '<td colspan="2" style="padding:8px;border:1px solid #ccc;"><b>المشروع / Project</b><br><span dir="ltr">{{ doc.project or "" }}</span></td>'
                '<td style="padding:8px;border:1px solid #ccc;"><b>أساس الفوترة</b><br>{{ doc.billing_basis or "" }}<br><small>Billing Basis</small></td>'
                '</tr></table>',
            ),
            _block(
                "description", "field", 48, 294, 694, 50,
                '<div style="direction:rtl;border:1px solid #ddd;background:#fafafa;padding:9px;font-size:12px;">'
                '<b>البيان / Description:</b> {{ doc.description or "فاتورة مبنية على الكميات المسلمة فعلياً" }}'
                '</div>',
            ),
            _block(
                "items", "field", 48, 360, 694, 310,
                '<table style="width:100%;table-layout:fixed;font-size:10px;border-collapse:collapse;direction:rtl;">'
                '<thead><tr style="background:#222;color:#fff;">'
                '<th style="width:4%;padding:7px 3px;border:1px solid #555;">#</th>'
                '<th style="width:17%;padding:7px 3px;border:1px solid #555;">الخدمة<br><small>Service</small></th>'
                '<th style="width:14%;padding:7px 3px;border:1px solid #555;">التاريخ<br><small>Date</small></th>'
                '<th style="width:20%;padding:7px 3px;border:1px solid #555;">الفندق<br><small>Hotel</small></th>'
                '<th style="width:10%;padding:7px 3px;border:1px solid #555;">الكمية<br><small>Qty</small></th>'
                '<th style="width:17%;padding:7px 3px;border:1px solid #555;">سعر الوحدة<br><small>Unit Price</small></th>'
                '<th style="width:18%;padding:7px 3px;border:1px solid #555;">الإجمالي<br><small>Amount</small></th>'
                '</tr></thead><tbody>'
                '{% for row in (doc.items or []) %}<tr>'
                '<td style="padding:7px 3px;border:1px solid #bbb;text-align:center;">{{ loop.index }}</td>'
                '<td style="padding:7px 3px;border:1px solid #bbb;">{{ row.meal_type or row.meal_plan or "" }}</td>'
                '<td style="padding:7px 3px;border:1px solid #bbb;text-align:center;">{{ frappe.utils.formatdate(row.service_date) if row.service_date else "" }}</td>'
                '<td style="padding:7px 3px;border:1px solid #bbb;">{{ row.hotel or "" }}</td>'
                '<td style="padding:7px 3px;border:1px solid #bbb;text-align:center;">{{ row.delivered_quantity or 0 }}</td>'
                '<td style="padding:7px 3px;border:1px solid #bbb;text-align:center;white-space:nowrap;">{{ frappe.utils.fmt_money(row.unit_price or 0, currency="SAR") }}</td>'
                '<td style="padding:7px 3px;border:1px solid #bbb;text-align:center;white-space:nowrap;">{{ frappe.utils.fmt_money(row.amount or 0, currency="SAR") }}</td>'
                '</tr>{% endfor %}'
                '{% if not doc.items %}<tr><td colspan="7" style="padding:16px;border:1px solid #bbb;text-align:center;color:#777;">لا توجد بنود / No items</td></tr>{% endif %}'
                '</tbody></table>',
            ),
            _block(
                "payment_note", "text", 48, 690, 330, 112,
                '<div style="direction:rtl;font-size:11px;line-height:1.8;border:1px solid #ddd;padding:11px;">'
                '<b>ملاحظات / Notes</b><br>تم إصدار هذه الفاتورة بناءً على الكميات المسلمة والمعتمدة في النظام.<br>'
                '<span dir="ltr">This invoice is generated from approved delivered quantities.</span>'
                '</div>',
            ),
            _block(
                "totals", "field", 405, 690, 337, 156,
                '<table style="width:100%;font-size:12px;border-collapse:collapse;direction:rtl;">'
                '<tr><td style="padding:7px;border-bottom:1px solid #ddd;">المجموع قبل الضريبة<br><small>Subtotal</small></td><td style="padding:7px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.subtotal or 0, currency="SAR") }}</td></tr>'
                '<tr><td style="padding:7px;border-bottom:1px solid #ddd;">الضريبة {{ doc.tax_rate or 0 }}%<br><small>VAT</small></td><td style="padding:7px;border-bottom:1px solid #ddd;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.tax_amount or 0, currency="SAR") }}</td></tr>'
                '<tr style="font-size:15px;font-weight:700;background:#f0e5c9;"><td style="padding:9px;">الإجمالي<br><small>Grand Total</small></td><td style="padding:9px;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.grand_total or 0, currency="SAR") }}</td></tr>'
                '<tr><td style="padding:7px;">المبلغ المحصل / Paid</td><td style="padding:7px;text-align:left;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.paid_amount or 0, currency="SAR") }}</td></tr>'
                '<tr><td style="padding:7px;font-weight:700;">الرصيد / Balance</td><td style="padding:7px;text-align:left;font-weight:700;white-space:nowrap;">{{ frappe.utils.fmt_money(doc.balance or 0, currency="SAR") }}</td></tr>'
                '</table>',
            ),
            _block(
                "status", "field", 48, 866, 694, 42,
                '<div style="direction:rtl;text-align:center;font-size:12px;border:1px solid #b88a2a;padding:9px;">'
                '<b>حالة الفاتورة / Status:</b> {{ doc.status or "" }}'
                '</div>',
            ),
            _block(
                "footer", "text", 48, 928, 694, 58,
                '<div style="border-top:1px solid #b88a2a;padding-top:9px;text-align:center;font-size:10px;color:#555;direction:rtl;line-height:1.7;">'
                'شركة وفد المدينة لخدمات الإعاشة — المدينة المنورة<br>'
                '<span dir="ltr">0500336989 &nbsp; | &nbsp; wafd.almadinah@gmail.com</span>'
                '</div>',
            ),
        ],
    }


def _apply_logo_to_all_templates():
    for name in frappe.get_all("WAFD Document Template", filters={"enabled": 1}, pluck="name"):
        doc = frappe.get_doc("WAFD Document Template", name)
        doc.logo = LOGO
        try:
            canvas = json.loads(doc.canvas_json or "{}")
        except Exception:
            canvas = {"version": 1, "blocks": []}
        blocks = canvas.setdefault("blocks", [])
        logo_blocks = [b for b in blocks if b.get("type") == "logo" or b.get("id") == "logo"]
        if logo_blocks:
            for block in logo_blocks:
                block["type"] = "logo"
                block["src"] = LOGO
        else:
            blocks.append(_block("company_logo", "logo", 650, 22, 92, 76, src=LOGO, z=20))
        doc.canvas_json = json.dumps(canvas, ensure_ascii=False)
        doc.save(ignore_permissions=True)


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return

    _apply_logo_to_all_templates()

    name = frappe.db.get_value(
        "WAFD Document Template",
        {"reference_doctype": "WAFD Invoice", "is_default": 1},
        "name",
    ) or frappe.db.get_value(
        "WAFD Document Template",
        {"reference_doctype": "WAFD Invoice", "enabled": 1},
        "name",
    )
    if name:
        doc = frappe.get_doc("WAFD Document Template", name)
    else:
        doc = frappe.get_doc({
            "doctype": "WAFD Document Template",
            "template_title": "الفاتورة الضريبية الاحترافية",
            "reference_doctype": "WAFD Invoice",
            "document_category": "Invoice",
            "enabled": 1,
        })

    doc.template_title = "الفاتورة الضريبية الاحترافية"
    doc.document_category = "Invoice"
    doc.enabled = 1
    doc.is_default = 1
    doc.logo = LOGO
    doc.page_size = "A4"
    doc.orientation = "Portrait"
    doc.direction = "RTL"
    doc.margin_top_mm = 4
    doc.margin_right_mm = 4
    doc.margin_bottom_mm = 4
    doc.margin_left_mm = 4
    doc.canvas_json = json.dumps(_invoice_canvas(), ensure_ascii=False)
    doc.custom_css = """
html, body { width: 100%; height: 100%; }
body { color: #111; }
table, tr, td, th { page-break-inside: avoid !important; }
.wds-print-page { page-break-after: avoid !important; page-break-inside: avoid !important; }
"""
    doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype="WAFD Document Template")
