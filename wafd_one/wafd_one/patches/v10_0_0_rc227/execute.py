from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import frappe
from frappe.utils import nowdate


def _norm_ar(value):
    value = (value or "").strip()
    for source, target in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        value = value.replace(source, target)
    value = re.sub(r"[\u064b-\u065f\u0670ـ\s\-\(\)\'\"]+", "", value)
    if value.startswith("فندق"):
        value = value[4:]
    return value


def _rows():
    path = Path(frappe.get_app_path("wafd_one")) / "reference_data" / "madinah_hotels_consolidated_rc227.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def execute():
    if not frappe.db.exists("DocType", "WAFD Hotel"):
        return

    # Re-apply the source permission matrix; stale Role Permission Manager rows
    # were the reason Undertaking Officers could see Add New yet fail to save.
    frappe.db.delete("Custom DocPerm", {
        "parent": "WAFD Hotel",
        "role": "WAFD Undertaking Officer",
    })
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True, reset_permissions=True)

    catalogue = _rows()
    by_key = {_norm_ar(r["hotel_name_ar"]): r for r in catalogue if _norm_ar(r["hotel_name_ar"])}

    existing = frappe.get_all(
        "WAFD Hotel",
        fields=["name", "hotel_name", "hotel_name_ar", "hotel_name_en"],
        limit_page_length=0,
    )
    matched_keys = set()

    for row in existing:
        key = _norm_ar(row.hotel_name_ar or row.hotel_name)
        target = by_key.get(key)
        if not target:
            continue
        matched_keys.add(key)
        values = {
            "hotel_name_ar": target["hotel_name_ar"].strip(),
            "hotel_name_en": target["hotel_name_en"].strip(),
            "city": (target.get("city") or "المدينة المنورة").strip(),
            "last_verified_on": nowdate(),
        }
        for fieldname in (
            "district", "zone_type", "proximity_band", "central_map_number",
            "central_sector", "distance_to_haram_km", "verification_status",
            "source_authority", "source_url", "source_map_edition", "source_notes",
        ):
            value = (target.get(fieldname) or "").strip()
            if value:
                values[fieldname] = value
        frappe.db.set_value("WAFD Hotel", row.name, values, update_modified=False)

    # Insert catalogue properties missing from the current site.  The consolidated
    # file is de-duplicated by normalized Arabic identity, so this does not create
    # another copy of already-matched records.
    for key, target in by_key.items():
        if key in matched_keys:
            continue
        doc = frappe.new_doc("WAFD Hotel")
        doc.hotel_name_ar = target["hotel_name_ar"].strip()
        doc.hotel_name_en = target["hotel_name_en"].strip()
        doc.hotel_name = doc.hotel_name_ar
        doc.city = (target.get("city") or "المدينة المنورة").strip()
        doc.district = (target.get("district") or "").strip()
        doc.status = "نشط / Active"
        doc.verification_status = (target.get("verification_status") or "يحتاج مراجعة / Needs Review").strip()
        for fieldname in (
            "zone_type", "proximity_band", "central_map_number", "central_sector",
            "distance_to_haram_km", "source_authority", "source_url",
            "source_map_edition", "source_notes",
        ):
            value = (target.get(fieldname) or "").strip()
            if value:
                setattr(doc, fieldname, value)
        doc.last_verified_on = nowdate()
        doc.insert(ignore_permissions=True)

    frappe.clear_cache(doctype="WAFD Hotel")
    frappe.clear_cache()
