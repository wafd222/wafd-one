from __future__ import annotations

import json
import frappe
from frappe.utils import now_datetime
from wafd_one.patches.v10_0_0_rc43.execute import _save_template

SERIES_KEYS = [
    "WAFD-INV-", "WAFD-INV-.#####", "WAFD-INVOICE-", "WAFD-INVOICE-.#####",
    "WAFD-PAY-", "WAFD-PAY-.#####", "WAFD-PRODUCTION-BATCH-", "WAFD-PRODUCTION-BATCH-.#####",
    "WAFD-QUALITY-INSPECTION-", "WAFD-QUALITY-INSPECTION-.#####", "WAFD-HC-", "WAFD-HC-.#####",
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
    """Ensure cabinets 1..50 without ever duplicating existing records.

    RC96 can be resumed safely after a partial migration. Existing rows are
    matched by asset code, sequence number, or the deterministic document name.
    Only missing cabinets are inserted.
    """
    frappe.reload_doc("wafd_one", "doctype", "wafd_hot_cabinet", force=True)
    for number in range(1, 51):
        code = f"HC-{number:03d}"
        expected_name = f"WAFD-HC-{number:05d}"

        name = (
            frappe.db.get_value("WAFD Hot Cabinet", {"asset_code": code}, "name")
            or frappe.db.get_value("WAFD Hot Cabinet", {"sequence_number": number}, "name")
            or (expected_name if frappe.db.exists("WAFD Hot Cabinet", expected_name) else None)
        )

        values = {
            "cabinet_name": f"سخان رقم {number}",
            "sequence_number": number,
            "asset_code": code,
            "capacity": 50,
        }
        if name:
            # Preserve operational status/location while repairing master data.
            frappe.db.set_value(
                "WAFD Hot Cabinet", name, values, update_modified=False
            )
            continue

        doc = frappe.get_doc({
            "doctype": "WAFD Hot Cabinet",
            "naming_series": "WAFD-HC-.#####",
            **values,
            "status": "متاح / Available",
        })
        try:
            doc.insert(ignore_permissions=True)
        except frappe.DuplicateEntryError:
            # A partially executed migration may already have consumed the name.
            # Locate and repair that row instead of aborting the whole migrate.
            existing = (
                frappe.db.get_value("WAFD Hot Cabinet", {"asset_code": code}, "name")
                or frappe.db.get_value("WAFD Hot Cabinet", {"sequence_number": number}, "name")
                or (expected_name if frappe.db.exists("WAFD Hot Cabinet", expected_name) else None)
            )
            if not existing:
                raise
            frappe.db.set_value(
                "WAFD Hot Cabinet", existing, values, update_modified=False
            )

def execute():
    _reset_series()
    _ensure_cabinets()
    if frappe.db.exists("DocType", "WAFD Document Template"):
        _save_template("WAFD Catering Project", "شهادة استلام وشكر", "Certificate", _certificate_canvas())
    frappe.clear_cache()
