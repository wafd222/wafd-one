"""Printable delivery execution report for management and delivery supervisors."""

from __future__ import annotations

from html import escape

import frappe
from frappe import _
from frappe.utils import cint, formatdate, get_datetime, getdate, nowdate

from wafd_one.delivery_supervisor import ALLOWED_ROLES, _delivery_clients


def _check_access():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("لا تملك صلاحية تقارير التوصيل / Delivery report access required"), frappe.PermissionError)


def _safe(value):
    return escape(str(value or ""))


def _filters(report_mode="all", company=None, hotel=None, from_date=None, to_date=None):
    filters = {"status": ["!=", "ملغية / Cancelled"]}
    if report_mode == "company":
        if not company:
            frappe.throw(_("اختر الشركة أو البعثة أو الجهة / Choose a company, mission or entity"))
        filters["contracting_entity"] = company
    elif report_mode == "hotel":
        if not hotel:
            frappe.throw(_("اختر الفندق / Choose a hotel"))
        filters["hotel"] = hotel
    if from_date:
        filters["trip_date"] = [">=", getdate(from_date)]
    if to_date:
        condition = ["<=", getdate(to_date)]
        if "trip_date" in filters:
            filters["trip_date"] = ["between", [getdate(from_date), getdate(to_date)]]
        else:
            filters["trip_date"] = condition
    return filters


def _rows(report_mode="all", company=None, hotel=None, from_date=None, to_date=None):
    rows = frappe.get_all(
        "WAFD Delivery Trip",
        filters=_filters(report_mode, company, hotel, from_date, to_date),
        fields=[
            "name", "trip_date", "contracting_entity", "schedule_customer", "destination_name",
            "hotel", "meal_type", "quantity", "safandash_count", "hot_cabinet_count",
            "driver", "vehicle", "status", "actual_arrival",
        ],
        order_by="trip_date asc, planned_arrival asc, creation asc",
        limit_page_length=5000,
    )
    names = [row.name for row in rows]
    proofs = frappe.get_all(
        "WAFD Delivery Proof",
        filters={"delivery_trip": ["in", names]},
        fields=["delivery_trip", "delivery_time", "receiver_name", "status"],
        limit_page_length=5000,
    ) if names else []
    proof_map = {row.delivery_trip: row for row in proofs}
    for row in rows:
        row["proof"] = proof_map.get(row.name)
    return rows


@frappe.whitelist()
def get_delivery_report_options():
    _check_access()
    companies = {row.client_name: row for row in _delivery_clients()}
    for name in frappe.get_all("WAFD Delivery Trip", filters={"contracting_entity": ["is", "set"]}, pluck="contracting_entity", distinct=True):
        companies.setdefault(name, {"name": name, "client_name": name, "client_type": ""})
    hotels = frappe.get_all(
        "WAFD Hotel", fields=["name", "hotel_name_ar", "hotel_name_en"],
        order_by="hotel_name_ar asc", limit_page_length=2000,
    )
    return {"today": nowdate(), "companies": list(companies.values()), "hotels": hotels}


def _period(from_date, to_date):
    if not from_date and not to_date:
        return "كامل المدة"
    return f"{formatdate(from_date or to_date, 'dd-MM-yyyy')} — {formatdate(to_date or from_date, 'dd-MM-yyyy')}"


def _report_html(report_mode="all", company=None, hotel=None, from_date=None, to_date=None):
    rows = _rows(report_mode, company, hotel, from_date, to_date)
    scope = "جميع الشركات والبعثات والفنادق"
    if report_mode == "company":
        scope = company
    elif report_mode == "hotel":
        scope = frappe.db.get_value("WAFD Hotel", hotel, "hotel_name_ar") or hotel
    totals = {
        "trips": len(rows), "delivered": sum(1 for r in rows if r.proof),
        "meals": sum(cint(r.quantity) for r in rows),
        "safandash": sum(cint(r.safandash_count) for r in rows),
        "heaters": sum(cint(r.hot_cabinet_count) for r in rows),
    }
    body = []
    for index, row in enumerate(rows, 1):
        proof = row.proof
        company_name = row.contracting_entity or row.schedule_customer or "—"
        destination = row.destination_name or row.hotel or "—"
        delivered = get_datetime(proof.delivery_time).strftime("%d-%m-%Y %H:%M") if proof and proof.delivery_time else "لم يتم التسليم"
        receiver = proof.receiver_name if proof else "—"
        body.append(f"""
        <tr><td>{index}</td><td dir='ltr'>{formatdate(row.trip_date, 'dd-MM-yyyy')}</td>
        <td><b>{_safe(company_name)}</b><small>{_safe(destination)}</small></td>
        <td><b>{_safe((row.meal_type or '').split('/')[0].strip())}</b><small>الوجبات: {cint(row.quantity)} · السفندشات: {cint(row.safandash_count)} · السخانات: {cint(row.hot_cabinet_count)}</small></td>
        <td><b>{_safe(row.driver or '—')}</b><small>{_safe(row.vehicle or '—')}</small></td>
        <td><b>{_safe(delivered)}</b><small>المستلم: {_safe(receiver)}</small></td></tr>""")
    if not body:
        body.append("<tr><td colspan='6' class='empty'>لا توجد عمليات مطابقة للفلاتر المحددة</td></tr>")
    return f"""<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><style>
@page{{size:A4 portrait;margin:8mm 14mm}}html,body{{margin:0;padding:0;background:#fff}}body{{font-family:Tahoma,Arial,sans-serif;color:#111;font-size:10px;line-height:1.55}}.sheet{{direction:rtl;box-sizing:border-box;padding:0 1mm}}.head{{display:table;width:100%;table-layout:fixed;border-bottom:1px solid #b88a2a;padding-bottom:3mm;margin-bottom:4mm}}.head>div{{display:table-cell;vertical-align:middle}}.head-left{{width:34%;text-align:left;font-size:8.8px;color:#555}}.head-center{{width:48%;text-align:center}}.head-center b{{font-size:15px}}.head-center span{{font-size:8.8px;color:#666}}.head-right{{width:18%;text-align:right}}.logo{{width:24mm;height:25mm;object-fit:contain}}h1{{text-align:center;font-size:16px;text-decoration:underline;margin:2mm 0 4mm}}.details,.summary,.report{{width:100%;border-collapse:collapse}}.details{{margin:3mm 0;font-size:9.7px}}.details td{{border:1px solid #bbb;padding:2.2mm;vertical-align:top}}.summary{{margin:3mm 0}}.summary td{{border:1px solid #d7c9aa;text-align:center;padding:2mm}}.summary b{{display:block;font-size:14px;color:#8b681b}}.summary small,.report small{{display:block;color:#666;margin-top:1mm}}.report{{table-layout:fixed;font-size:8.2px}}.report th{{background:#1d1f22;color:#fff;padding:2mm 1mm;border:1px solid #444}}.report td{{border:1px solid #ccc;padding:2mm 1.3mm;vertical-align:top;overflow-wrap:anywhere}}.report th:nth-child(1){{width:4%}}.report th:nth-child(2){{width:11%}}.report th:nth-child(3){{width:27%}}.report th:nth-child(4){{width:22%}}.report th:nth-child(5){{width:16%}}.report th:nth-child(6){{width:20%}}thead{{display:table-header-group}}tr{{page-break-inside:avoid}}.empty{{text-align:center;padding:15mm!important;color:#777}}.footer{{border-top:1px solid #b88a2a;margin-top:5mm;padding-top:2mm;text-align:center;font-size:8px;color:#666}}
</style></head><body><div class='sheet'><div class='head'><div class='head-left'><div>المدينة المنورة — حي الملك فهد</div><div dir='ltr'>0500336989</div><div dir='ltr'>wafd.almadinah@gmail.com</div></div><div class='head-center'><b>شركة وفد المدينة لخدمات الإعاشة</b><br><span>WAFD AL-MADINAH CATERING SERVICES</span></div><div class='head-right'><img class='logo' src='/assets/wafd_one/images/wafd-almadinah-official.png'></div></div><h1>تقرير تنفيذ وتسليم الوجبات</h1>
<table class='details'><tr><td><b>نطاق التقرير</b><br>{_safe(scope)}</td><td><b>الفترة</b><br><span dir='ltr'>{_safe(_period(from_date,to_date))}</span></td></tr><tr><td><b>تاريخ الإصدار</b><br><span dir='ltr'>{formatdate(nowdate(),'dd-MM-yyyy')}</span></td><td><b>السجل التجاري</b><br>7051832694</td></tr></table>
<table class='summary'><tr><td><b>{totals['trips']}</b><small>إجمالي الرحلات</small></td><td><b>{totals['delivered']}</b><small>التسليمات الموثقة</small></td><td><b>{totals['meals']}</b><small>الوجبات</small></td><td><b>{totals['safandash']}</b><small>السفندشات</small></td><td><b>{totals['heaters']}</b><small>السخانات</small></td></tr></table>
<table class='report'><thead><tr><th>م</th><th>التاريخ</th><th>الشركة أو البعثة<br>الفندق أو الجهة</th><th>الوجبة والكميات</th><th>السائق والمركبة</th><th>التسليم والمستلم</th></tr></thead><tbody>{''.join(body)}</tbody></table>
<div class='footer'>شركة وفد المدينة لخدمات الإعاشة — WAFD ONE</div></div></body></html>"""


@frappe.whitelist()
def download_delivery_report_pdf(report_mode="all", company=None, hotel=None, from_date=None, to_date=None, download=1):
    _check_access()
    from frappe.utils.pdf import get_pdf
    from wafd_one.document_studio import _embed_pdf_images
    pdf = get_pdf(_embed_pdf_images(_report_html(report_mode, company, hotel, from_date, to_date)), options={
        "page-size": "A4", "orientation": "Portrait", "margin-top": "0mm", "margin-right": "0mm",
        "margin-bottom": "0mm", "margin-left": "0mm", "encoding": "UTF-8", "print-media-type": None,
    })
    frappe.local.response.filename = f"wafd-delivery-report-{nowdate()}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"
    if not cint(download):
        frappe.local.response.display_content_as = "inline"
