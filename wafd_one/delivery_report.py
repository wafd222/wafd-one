"""Read-only operational delivery reports for management and delivery supervisors."""

from __future__ import annotations

from html import escape
import frappe
from frappe import _
from frappe.utils import cint, format_date, format_datetime, getdate


ALLOWED_ROLES = {"System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"}


def _check_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("هذه التقارير للإدارة ومشرف التوصيل فقط / Report access denied"), frappe.PermissionError)


def _text(value, default="—"):
    return escape(str(value if value not in (None, "") else default), quote=True)


def _local(value):
    parts = [part.strip() for part in str(value or "").split("/")]
    return parts[0] if parts else ""


def _report_rows(from_date=None, to_date=None, contracting_entity=None, hotel=None):
    filters = {"status": ["!=", "ملغية / Cancelled"]}
    if from_date and to_date:
        filters["trip_date"] = ["between", [getdate(from_date), getdate(to_date)]]
    elif from_date:
        filters["trip_date"] = [">=", getdate(from_date)]
    elif to_date:
        filters["trip_date"] = ["<=", getdate(to_date)]
    if hotel:
        filters["hotel"] = hotel

    rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters=filters,
        fields=[
            "name", "trip_date", "contracting_entity", "schedule_customer", "destination_name",
            "hotel", "delivery_location", "meal_type", "quantity", "safandash_count",
            "hot_cabinet_count", "driver", "vehicle", "planned_arrival", "actual_departure",
            "actual_arrival", "status", "contract", "project",
        ],
        order_by="trip_date asc, planned_arrival asc, creation asc",
        limit_page_length=5000,
    )
    company = (contracting_entity or "").strip()
    if company:
        rows = [row for row in rows if (row.contracting_entity or row.schedule_customer or "").strip() == company]

    proof_rows = frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": ["in", [row.name for row in rows]]},
        fields=["delivery_trip", "delivery_time", "receiver_name", "delivery_photo", "received_quantity"],
        order_by="delivery_time desc",
        limit_page_length=5000,
    ) if rows else []
    proof_map = {}
    for proof in proof_rows:
        proof_map.setdefault(proof.delivery_trip, proof)

    hotel_names = list({row.hotel for row in rows if row.hotel})
    hotel_map = {
        row.name: (row.hotel_name_ar or row.hotel_name_en or row.name)
        for row in frappe.get_all(
            "WAFD Hotel", filters={"name": ["in", hotel_names]},
            fields=["name", "hotel_name_ar", "hotel_name_en"], limit_page_length=2000,
        )
    } if hotel_names else {}
    driver_names = list({row.driver for row in rows if row.driver})
    driver_map = {
        row.name: (row.driver_name or row.name)
        for row in frappe.get_all(
            "WAFD Driver", filters={"name": ["in", driver_names]},
            fields=["name", "driver_name"], limit_page_length=1000,
        )
    } if driver_names else {}

    for row in rows:
        row["company"] = row.contracting_entity or row.schedule_customer or "—"
        row["destination"] = hotel_map.get(row.hotel) or row.destination_name or row.delivery_location or row.hotel or "—"
        row["driver_display"] = driver_map.get(row.driver, row.driver or "—")
        row["proof"] = proof_map.get(row.name)
    return rows


@frappe.whitelist()
def get_delivery_report_options():
    _check_access()
    rows = frappe.get_all(
        "WAFD Delivery Trip", filters={"status": ["!=", "ملغية / Cancelled"]},
        fields=["trip_date", "contracting_entity", "schedule_customer", "hotel"],
        order_by="trip_date desc", limit_page_length=5000,
    )
    companies = sorted({(row.contracting_entity or row.schedule_customer or "").strip() for row in rows if (row.contracting_entity or row.schedule_customer)})
    hotel_names = sorted({row.hotel for row in rows if row.hotel})
    hotels = frappe.get_all(
        "WAFD Hotel", filters={"name": ["in", hotel_names]}, fields=["name", "hotel_name_ar", "hotel_name_en"],
        order_by="hotel_name_ar asc", limit_page_length=2000,
    ) if hotel_names else []
    dates = [getdate(row.trip_date) for row in rows if row.trip_date]
    return {
        "companies": companies, "hotels": hotels,
        "first_date": min(dates).isoformat() if dates else None,
        "last_date": max(dates).isoformat() if dates else None,
    }


def _render_report_html(from_date=None, to_date=None, contracting_entity=None, hotel=None):
    rows = _report_rows(from_date, to_date, contracting_entity, hotel)
    delivered = sum(1 for row in rows if row.proof)
    meals = sum(cint(row.quantity) for row in rows)
    safandash = sum(cint(row.safandash_count) for row in rows)
    cabinets = sum(cint(row.hot_cabinet_count) for row in rows)
    hotel_title = ""
    if hotel:
        hotel_title = frappe.db.get_value("WAFD Hotel", hotel, "hotel_name_ar") or hotel
    scope = contracting_entity or hotel_title or "جميع الشركات والبعثات والفنادق"
    if from_date or to_date:
        period = f"{format_date(from_date) if from_date else 'البداية'} — {format_date(to_date) if to_date else 'حتى اليوم'}"
    else:
        period = "كامل المدة"

    body_rows = []
    for index, row in enumerate(rows, 1):
        proof = row.proof
        delivery = format_datetime(proof.delivery_time, "dd-MM-yyyy HH:mm") if proof and proof.delivery_time else "لم يتم التسليم"
        receiver = proof.receiver_name if proof else "—"
        body_rows.append(
            "<tr>"
            f"<td>{index}</td><td>{_text(format_date(row.trip_date))}</td>"
            f"<td>{_text(row.company)}</td><td>{_text(row.destination)}</td>"
            f"<td>{_text(_local(row.meal_type))}</td><td>{cint(row.quantity)}</td>"
            f"<td>{cint(row.safandash_count) or '—'}</td><td>{cint(row.hot_cabinet_count) or '—'}</td>"
            f"<td>{_text(row.driver_display)}<small>{_text(row.vehicle, '')}</small></td>"
            f"<td>{_text(delivery)}<small>{_text(receiver, '')}</small></td>"
            "</tr>"
        )
    if not body_rows:
        body_rows.append('<tr><td colspan="10" class="empty">لا توجد عمليات توصيل مطابقة للاختيار</td></tr>')

    return f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><style>
@page{{size:A4 landscape;margin:12mm 10mm 17mm}}*{{box-sizing:border-box}}body{{font-family:"DejaVu Sans",Arial,sans-serif;color:#202124;margin:0;font-size:10px;direction:rtl}}
.sheet{{border-top:2px solid #c99b2b;padding-top:8px}}.head{{width:100%;border-bottom:1px solid #d3b15e;padding-bottom:8px;margin-bottom:10px}}.head td{{vertical-align:middle}}.logo{{width:76px;max-height:70px;object-fit:contain}}h1{{font-size:19px;margin:0 0 3px}}.en{{color:#8b6a1e;font-weight:bold;letter-spacing:.5px}}.meta{{text-align:left;color:#666;line-height:1.8}}
.scope{{border:1px solid #e3d8bf;background:#faf8f3;border-radius:8px;padding:8px 10px;margin-bottom:9px}}.summary{{width:100%;border-spacing:6px;margin:0 -6px 8px}}.summary td{{border:1px solid #e2d8c4;border-radius:7px;padding:7px;text-align:center}}.summary b{{display:block;font-size:17px;color:#8b6817}}.summary small{{color:#6e7278}}
table.data{{width:100%;border-collapse:collapse;table-layout:fixed}}.data th{{background:#202124;color:#fff;padding:7px 4px;font-size:9px}}.data td{{border:1px solid #ded8cc;padding:6px 4px;vertical-align:top;text-align:center;word-wrap:break-word}}.data tr:nth-child(even) td{{background:#faf9f6}}.data small{{display:block;color:#777;margin-top:3px;font-size:8px}}.data .empty{{padding:30px;color:#777;font-size:13px}}.footer{{position:fixed;bottom:-12mm;left:0;right:0;border-top:1px solid #c99b2b;padding-top:5px;text-align:center;color:#666;font-size:8px}}.no{{width:25px}}.date{{width:60px}}.qty{{width:48px}}.driver{{width:80px}}.delivery{{width:112px}}
</style></head><body><div class="sheet"><table class="head"><tr><td><img class="logo" src="/assets/wafd_one/images/wafd-almadinah-official.png"></td><td><h1>تقرير تنفيذ وتسليم الوجبات</h1><div class="en">MEAL DELIVERY EXECUTION REPORT</div></td><td class="meta">تاريخ الإصدار: {_text(format_date(frappe.utils.nowdate()))}<br>أعده: {_text(frappe.utils.get_fullname(frappe.session.user))}</td></tr></table>
<div class="scope"><b>نطاق التقرير:</b> {_text(scope)} &nbsp; | &nbsp; <b>الفترة:</b> {_text(period)}</div>
<table class="summary"><tr><td><b>{len(rows)}</b><small>إجمالي الرحلات</small></td><td><b>{delivered}</b><small>التسليمات الموثقة</small></td><td><b>{meals}</b><small>عدد الوجبات</small></td><td><b>{safandash}</b><small>عدد السفندشات</small></td><td><b>{cabinets}</b><small>عدد السخانات Hot Cabinet</small></td></tr></table>
<table class="data"><thead><tr><th class="no">م</th><th class="date">التاريخ</th><th>الشركة أو البعثة أو الجهة</th><th>الفندق أو موقع التسليم</th><th>الوجبة</th><th class="qty">الوجبات</th><th class="qty">السفندشات</th><th class="qty">السخانات</th><th class="driver">السائق / المركبة</th><th class="delivery">التسليم / المستلم</th></tr></thead><tbody>{''.join(body_rows)}</tbody></table>
</div><div class="footer">شركة وفد المدينة لخدمات الإعاشة — WAFD AL MADINAH CATERING SERVICES &nbsp; | &nbsp; تقرير صادر من نظام WAFD ONE</div></body></html>"""


@frappe.whitelist()
def preview_delivery_report_html(from_date=None, to_date=None, contracting_entity=None, hotel=None):
    _check_access()
    from wafd_one.document_studio import _embed_pdf_images
    report_html = _embed_pdf_images(_render_report_html(from_date, to_date, contracting_entity, hotel))
    frappe.local.response.filename = "delivery-report.html"
    frappe.local.response.filecontent = report_html.encode("utf-8")
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "inline"
    frappe.local.response.content_type = "text/html; charset=utf-8"


@frappe.whitelist()
def download_delivery_report_pdf(from_date=None, to_date=None, contracting_entity=None, hotel=None, download=0):
    _check_access()
    from frappe.utils.pdf import get_pdf
    from wafd_one.document_studio import _embed_pdf_images, _remove_trailing_blank_pages
    report_html = _embed_pdf_images(_render_report_html(from_date, to_date, contracting_entity, hotel))
    pdf = get_pdf(report_html, options={
        "page-size": "A4", "orientation": "Landscape", "margin-top": "0mm", "margin-right": "0mm",
        "margin-bottom": "0mm", "margin-left": "0mm", "encoding": "UTF-8", "print-media-type": None,
    })
    pdf = _remove_trailing_blank_pages(pdf)
    frappe.local.response.filename = f"WAFD-Delivery-Report-{frappe.utils.nowdate()}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
    frappe.local.response.display_content_as = "attachment" if cint(download) else "inline"
    frappe.local.response.content_type = "application/pdf"
