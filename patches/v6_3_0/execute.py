from __future__ import annotations
import csv
from pathlib import Path
import frappe
from frappe.utils import nowdate

DATA_FILE = "madinah_hotels_400_ota_review.csv"

def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True)
    path = Path(frappe.get_app_path("wafd_one")) / "reference_data" / DATA_FILE
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        for row in rows:
            hotel_name = (row.get("hotel_name") or "").strip()
            if not hotel_name:
                continue
            existing = frappe.db.get_value("WAFD Hotel", {"hotel_name": hotel_name}, "name")
            if existing:
                doc = frappe.get_doc("WAFD Hotel", existing)
                changed = False
                for fieldname in ("city", "district", "address", "source_authority", "source_url"):
                    value = (row.get(fieldname) or "").strip()
                    if value and not doc.get(fieldname):
                        doc.set(fieldname, value); changed = True
                if not doc.get("verification_status"):
                    doc.verification_status = "يحتاج مراجعة / Needs Review"; changed = True
                if changed:
                    doc.save(ignore_permissions=True)
            else:
                doc = frappe.new_doc("WAFD Hotel")
                doc.hotel_name = hotel_name
                doc.status = "نشط / Active"
                doc.city = row.get("city") or "المدينة المنورة"
                doc.district = row.get("district")
                doc.address = row.get("address")
                doc.verification_status = "يحتاج مراجعة / Needs Review"
                doc.source_authority = row.get("source_authority")
                doc.source_url = row.get("source_url")
                doc.source_notes = row.get("verification_status")
                doc.last_verified_on = nowdate()
                doc.insert(ignore_permissions=True)
