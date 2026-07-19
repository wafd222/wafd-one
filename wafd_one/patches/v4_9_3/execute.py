from __future__ import annotations
import csv
from pathlib import Path
import frappe
from frappe.utils import nowdate

DATA_FILE = "madinah_central_area_official_map_2026.csv"

def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True)
    path = Path(frappe.get_app_path("wafd_one")) / "reference_data" / DATA_FILE
    if not path.exists():
        frappe.throw(f"Missing reference data file: {DATA_FILE}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        hotel_name = (row.get("hotel_name") or "").strip()
        map_no = (row.get("central_map_number") or "").strip()
        if not hotel_name:
            continue
        existing = frappe.db.get_value("WAFD Hotel", {"hotel_name": hotel_name}, "name")
        if not existing and map_no:
            existing = frappe.db.get_value("WAFD Hotel", {"central_map_number": map_no}, "name")
        doc = frappe.get_doc("WAFD Hotel", existing) if existing else frappe.new_doc("WAFD Hotel")
        if not existing:
            doc.hotel_name = hotel_name
            doc.status = "نشط / Active"
        values = {
            "city": row.get("city"), "district": row.get("district"),
            "zone_type": row.get("zone_type"), "central_map_number": map_no,
            "central_sector": row.get("central_sector"), "source_authority": row.get("source_authority"),
            "source_map_edition": row.get("source_map_edition"), "verification_status": row.get("verification_status"),
            "source_notes": row.get("source_notes"), "last_verified_on": nowdate(),
        }
        for field, value in values.items():
            if value:
                doc.set(field, value)
        doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)
    frappe.db.commit()
