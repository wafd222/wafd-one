from __future__ import annotations

import json
import frappe
from frappe.utils import now_datetime
from wafd_one.patches.v10_0_0_rc43.execute import _save_template

SERIES_KEYS = [
    "WAFD-INV-", "WAFD-INV-.#####", "WAFD-INVOICE-", "WAFD-INVOICE-.#####",
    "WAFD-PAY-", "WAFD-PAY-.#####", "WAFD-PRODUCTION-BATCH-", "WAFD-PRODUCTION-BATCH-.#####",
    "WAFD-QUALITY-INSPECTION-", "WAFD-QUALITY-INSPECTION-.#####",
]

def _certificate_canvas():
    html = """<div style='direction:rtl;text-align:center;font-family:Arial;padding:35px;border:2px solid #b88a2a;height:980px;box-sizing:border-box;'>
    <h2 style='margin-top:35px'>شركة وفد المدينة لخدمات الإعاشة</h2><div style='color:#666'>WAFD AL-MADINAH CATERING SERVICES</div>
    <hr style='border:0;border-top:2px solid #b88a2a;margin:25px 0'><h1>شهادة استلام وشكر</h1><div style='font-size:18px'>SERVICE ACCEPTANCE & APPRECIATION CERTIFICATE</div>
    <p style='font-size:16px;line-height:2.3;margin:55px 35px'>نشهد نحن <b>{{ doc.mission or doc.client_name or "الجهة المستفيدة" }}</b> بأن شركة وفد المدينة لخدمات الإعاشة قد أتمت تقديم خدمات الإعاشة للمشروع <b>{{ doc.project_name or doc.name }}</b> في فندق <b>{{ doc.primary_hotel or "................" }}</b>، وتم استلام الخدمات وفق الكميات والمواصفات المتفق عليها.</p>
    <table style='width:100%;border-collapse:collapse;font-size:14px'><tr><td style='border:1px solid #ddd;padding:12px'>رقم المشروع<br>{{ doc.name }}</td><td style='border:1px solid #ddd;padding:12px'>الفترة<br>{{ doc.start_date or "" }} — {{ doc.end_date or "" }}</td></tr></table>
    <div style='display:flex;justify-content:space-between;margin-top:100px;font-size:14px'><div>اسم ممثل الفندق/المشرف<br><br>____________________</div><div>التوقيع والختم<br><br><br>____________________</div><div>التاريخ<br><br>____________________</div></div>
    <div style='position:absolute;bottom:45px;left:60px;right:60px;border-top:1px solid #b88a2a;padding-top:10px;font-size:11px'>0500336989 | شركة وفد المدينة لخدمات الإعاشة — المدينة المنورة</div></div>"""
    return {"page":{"width":794,"height":1123,"background":"#fff"},"blocks":[{"id":"certificate","type":"html","x":20,"y":20,"w":754,"h":1083,"html":html}]}

def _reset_series():
    if not frappe.db.table_exists("Series"):
        return
    for key in SERIES_KEYS:
        frappe.db.sql("delete from `tabSeries` where name=%s", key)

def _ensure_cabinets():
    """Ensure cabinets 1..50 safely after partial or repeated migrations.

    Cabinet names are deterministic. Existing rows are repaired in place and
    missing rows are inserted with duplicate protection. This avoids consuming
    the naming series again when RC96 is retried after a failed migrate.
    """
    frappe.reload_doc("wafd_one", "doctype", "wafd_hot_cabinet", force=True)

    for number in range(1, 51):
        code = f"HC-{number:03d}"
        expected_name = f"WAFD-HC-{number:05d}"
        values = {
            "cabinet_name": f"سخان رقم {number}",
            "sequence_number": number,
            "asset_code": code,
            "capacity": 50,
        }

        existing = (
            (expected_name if frappe.db.exists("WAFD Hot Cabinet", expected_name) else None)
            or frappe.db.get_value("WAFD Hot Cabinet", {"asset_code": code}, "name")
            or frappe.db.get_value("WAFD Hot Cabinet", {"sequence_number": number}, "name")
        )
        if existing:
            frappe.db.set_value("WAFD Hot Cabinet", existing, values, update_modified=False)
            continue

        doc = frappe.get_doc({
            "doctype": "WAFD Hot Cabinet",
            "name": expected_name,
            **values,
            "status": "متاح / Available",
        })
        # Frappe may retry a failed patch after a row was already committed.
        # ignore_if_duplicate prevents that harmless state from aborting migrate.
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)

        actual = (
            (expected_name if frappe.db.exists("WAFD Hot Cabinet", expected_name) else None)
            or frappe.db.get_value("WAFD Hot Cabinet", {"asset_code": code}, "name")
            or frappe.db.get_value("WAFD Hot Cabinet", {"sequence_number": number}, "name")
        )
        if actual:
            frappe.db.set_value("WAFD Hot Cabinet", actual, values, update_modified=False)

def execute():
    _reset_series()
    _ensure_cabinets()
    if frappe.db.exists("DocType", "WAFD Document Template"):
        _save_template("WAFD Catering Project", "شهادة استلام وشكر", "Certificate", _certificate_canvas())
    frappe.clear_cache()
