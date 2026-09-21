"""Load the phase-one Madinah Central Area hotel directory.

The patch is idempotent and never deletes operational hotel records. Existing
records are enriched only where a field is empty.
"""
from __future__ import annotations

import csv
from pathlib import Path

import frappe
from frappe.utils import nowdate


DATA_FILE = "madinah_central_area_hotels_phase1.csv"


def _empty(value):
    return value in (None, "")


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True)
    path = Path(frappe.get_app_path("wafd_one")) / "reference_data" / DATA_FILE
    if not path.exists():
        frappe.throw(f"Missing reference data file: {DATA_FILE}")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        name = (row.get("hotel_name") or "").strip()
        if not name:
            continue

        existing = frappe.db.get_value("WAFD Hotel", {"hotel_name": name}, "name")
        if existing:
            doc = frappe.get_doc("WAFD Hotel", existing)
        else:
            doc = frappe.new_doc("WAFD Hotel")
            doc.hotel_name = name
            doc.status = "نشط / Active"

        updates = {
            "city": row.get("city") or "المدينة المنورة",
            "district": row.get("district"),
            "address": row.get("address"),
            "zone_type": "المنطقة المركزية / Central Zone",
            "source_authority": "Booking / Expedia / Agoda / Central hotel directories",
            "source_url": row.get("booking_search_url"),
            "verification_status": "يحتاج مراجعة / Needs Review",
            "last_verified_on": nowdate(),
            "source_notes": row.get("source_status"),
            "booking_listed": 1,
            "expedia_listed": 1,
            "agoda_listed": 1,
            "listing_checked_on": nowdate(),
        }
        for field, value in updates.items():
            if not value:
                continue
            if not existing or _empty(doc.get(field)) or field in {
                "zone_type", "verification_status", "last_verified_on",
                "source_notes", "booking_listed", "expedia_listed",
                "agoda_listed", "listing_checked_on"
            }:
                doc.set(field, value)

        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)

