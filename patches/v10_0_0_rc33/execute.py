import json

import frappe


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
        "font_size": kwargs.pop("font_size", 14),
        "color": kwargs.pop("color", "#111111"),
        "background": kwargs.pop("background", "transparent"),
        "opacity": 1,
        "rotation": 0,
    }
    value.update(kwargs)
    return value


def _invoice_canvas():
    return {
        "version": 2,
        "blocks": [
            _block(
                "brand",
                "text",
                45,
                30,
                700,
                74,
                '<div style="direction:rtl;border-bottom:3px solid #b88a2a;padding-bottom:14px;">'
                '<div style="font-size:23px;font-weight:700;">شركة وفد المدينة لخدمات الإعاشة</div>'
                '<div style="font-size:12px;color:#555;margin-top:5px;">WAFD AL-MADINAH CATERING SERVICES</div>'
                '</div>',
            ),
            _block(
                "title",
                "text",
                45,
                120,
                700,
                55,
                '<div style="text-align:center;font-size:28px;font-weight:700;color:#191919;">فاتورة ضريبية</div>'
                '<div style="text-align:center;font-size:14px;color:#666;">TAX INVOICE</div>',
            ),
            _block(
                "meta",
                "field",
                45,
                190,
                700,
                92,
                '<table style="width:100%;font-size:13px;border:1px solid #d7d7d7;">'
                '<tr>'
                '<td style="padding:8px;border:1px solid #d7d7d7;"><b>رقم الفاتورة / Invoice No.</b><br>{{ doc.name or "" }}</td>'
                '<td style="padding:8px;border:1px solid #d7d7d7;"><b>تاريخ الفاتورة / Invoice Date</b><br>{{ frappe.utils.formatdate(doc.invoice_date) if doc.invoice_date else "" }}</td>'
                '<td style="padding:8px;border:1px solid #d7d7d7;"><b>تاريخ الاستحقاق / Due Date</b><br>{{ frappe.utils.formatdate(doc.due_date) if doc.due_date else "" }}</td>'
                '</tr>'
                '<tr>'
                '<td colspan="2" style="padding:8px;border:1px solid #d7d7d7;"><b>المشروع / Project</b><br>{{ doc.project or "" }}</td>'
                '<td style="padding:8px;border:1px solid #d7d7d7;"><b>أساس الفوترة / Billing Basis</b><br>{{ doc.billing_basis or "" }}</td>'
                '</tr>'
                '</table>',
            ),
            _block(
                "description",
                "field",
                45,
                296,
                700,
                58,
                '<div style="direction:rtl;border:1px solid #e1e1e1;background:#fafafa;padding:10px;font-size:13px;">'
                '<b>البيان / Description:</b> {{ doc.description or "فاتورة مبنية على الكميات المسلمة فعلياً" }}'
                '</div>',
            ),
            _block(
                "items",
                "field",
                45,
                372,
                700,
                350,
                '<table style="width:100%;font-size:11px;border-collapse:collapse;direction:rtl;">'
                '<thead><tr style="background:#222;color:#fff;">'
                '<th style="padding:8px;border:1px solid #555;">#</th>'
                '<th style="padding:8px;border:1px solid #555;">الخدمة / Service</th>'
                '<th style="padding:8px;border:1px solid #555;">التاريخ / Date</th>'
                '<th style="padding:8px;border:1px solid #555;">الفندق / Hotel</th>'
                '<th style="padding:8px;border:1px solid #555;">الكمية / Qty</th>'
                '<th style="padding:8px;border:1px solid #555;">سعر الوحدة / Unit Price</th>'
                '<th style="padding:8px;border:1px solid #555;">الإجمالي / Amount</th>'
                '</tr></thead><tbody>'
                '{% for row in (doc.items or []) %}'
                '<tr>'
                '<td style="padding:7px;border:1px solid #bbb;text-align:center;">{{ loop.index }}</td>'
                '<td style="padding:7px;border:1px solid #bbb;">{{ row.meal_type or row.meal_plan or "" }}</td>'
                '<td style="padding:7px;border:1px solid #bbb;text-align:center;">{{ frappe.utils.formatdate(row.service_date) if row.service_date else "" }}</td>'
                '<td style="padding:7px;border:1px solid #bbb;">{{ row.hotel or "" }}</td>'
                '<td style="padding:7px;border:1px solid #bbb;text-align:center;">{{ row.delivered_quantity or 0 }}</td>'
                '<td style="padding:7px;border:1px solid #bbb;text-align:center;">{{ frappe.utils.fmt_money(row.unit_price or 0, currency="SAR") }}</td>'
                '<td style="padding:7px;border:1px solid #bbb;text-align:center;">{{ frappe.utils.fmt_money(row.amount or 0, currency="SAR") }}</td>'
                '</tr>'
                '{% endfor %}'
                '{% if not doc.items %}<tr><td colspan="7" style="padding:18px;border:1px solid #bbb;text-align:center;color:#777;">لا توجد بنود / No items</td></tr>{% endif %}'
                '</tbody></table>',
            ),
            _block(
                "totals",
                "field",
                425,
                745,
                320,
                155,
                '<table style="width:100%;font-size:13px;border-collapse:collapse;direction:rtl;">'
                '<tr><td style="padding:7px;border-bottom:1px solid #ddd;">المجموع قبل الضريبة / Subtotal</td><td style="padding:7px;border-bottom:1px solid #ddd;text-align:left;">{{ frappe.utils.fmt_money(doc.subtotal or 0, currency="SAR") }}</td></tr>'
                '<tr><td style="padding:7px;border-bottom:1px solid #ddd;">الضريبة {{ doc.tax_rate or 0 }}% / VAT</td><td style="padding:7px;border-bottom:1px solid #ddd;text-align:left;">{{ frappe.utils.fmt_money(doc.tax_amount or 0, currency="SAR") }}</td></tr>'
                '<tr style="font-size:16px;font-weight:700;background:#f0e5c9;"><td style="padding:10px;">الإجمالي / Grand Total</td><td style="padding:10px;text-align:left;">{{ frappe.utils.fmt_money(doc.grand_total or 0, currency="SAR") }}</td></tr>'
                '<tr><td style="padding:7px;">المبلغ المحصل / Paid</td><td style="padding:7px;text-align:left;">{{ frappe.utils.fmt_money(doc.paid_amount or 0, currency="SAR") }}</td></tr>'
                '<tr><td style="padding:7px;font-weight:700;">الرصيد / Balance</td><td style="padding:7px;text-align:left;font-weight:700;">{{ frappe.utils.fmt_money(doc.balance or 0, currency="SAR") }}</td></tr>'
                '</table>',
            ),
            _block(
                "payment_note",
                "text",
                45,
                760,
                335,
                120,
                '<div style="direction:rtl;font-size:12px;line-height:1.9;border:1px solid #ddd;padding:12px;">'
                '<b>ملاحظات / Notes</b><br>'
                'تم إصدار هذه الفاتورة بناءً على الكميات المسلمة والمعتمدة في النظام.<br>'
                'This invoice is generated from approved delivered quantities.'
                '</div>',
            ),
            _block(
                "status",
                "field",
                45,
                905,
                700,
                45,
                '<div style="direction:rtl;text-align:center;font-size:13px;border:1px solid #b88a2a;padding:10px;">'
                '<b>حالة الفاتورة / Status:</b> {{ doc.status or "" }}'
                '</div>',
            ),
            _block(
                "footer",
                "text",
                45,
                975,
                700,
                66,
                '<div style="border-top:1px solid #b88a2a;padding-top:10px;text-align:center;font-size:11px;color:#555;direction:rtl;">'
                'شركة وفد المدينة لخدمات الإعاشة — المدينة المنورة<br>'
                'هاتف: 0500336989 &nbsp; | &nbsp; البريد: wafd.almadinah@gmail.com'
                '</div>',
            ),
        ],
    }


def execute():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return

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
    doc.page_size = "A4"
    doc.orientation = "Portrait"
    doc.direction = "RTL"
    doc.margin_top_mm = 6
    doc.margin_right_mm = 6
    doc.margin_bottom_mm = 6
    doc.margin_left_mm = 6
    doc.canvas_json = json.dumps(_invoice_canvas(), ensure_ascii=False)
    doc.custom_css = """
body { color: #111; }
table { page-break-inside: avoid; }
"""
    doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype="WAFD Document Template")
