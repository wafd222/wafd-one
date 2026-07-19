"""Import the official 2026 Madinah Central Area hotel map safely.

This patch is idempotent. It normalizes all Select-field values against the
installed WAFD Hotel metadata before saving, so a reference-data label cannot
break site migration.
"""
from __future__ import annotations

import csv
from pathlib import Path

import frappe
from frappe.utils import nowdate


DATA_FILE = "madinah_central_area_official_map_2026.csv"
MAP_VERIFICATION_STATUS = "رسمي موثق / Official Verified"
DEFAULT_STATUS = "نشط / Active"
DEFAULT_ZONE = "المنطقة المركزية / Central Zone"


def _clean(value):
    return (value or "").strip()


def _select_options(meta, fieldname):
    field = meta.get_field(fieldname)
    if not field or field.fieldtype != "Select":
        return set()
    return {
        option.strip()
        for option in (field.options or "").splitlines()
        if option.strip()
    }


def _safe_select(meta, fieldname, value, fallback=None):
    value = _clean(value)
    allowed = _select_options(meta, fieldname)
    if not allowed:
        return value or fallback
    if value in allowed:
        return value
    if fallback in allowed:
        return fallback
    return None


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True)
    meta = frappe.get_meta("WAFD Hotel", cached=False)

    path = Path(frappe.get_app_path("wafd_one")) / "reference_data" / DATA_FILE
    if not path.exists():
        frappe.throw(f"Missing reference data file: {DATA_FILE}")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        hotel_name = _clean(row.get("hotel_name"))
        map_no = _clean(row.get("central_map_number"))
        if not hotel_name:
            continue

        # Hotel name is the stable unique key in WAFD Hotel. The official map
        # can contain a repeated map number for distinct property names, so a
        # map-number lookup must not merge two hotels into one record.
        existing = frappe.db.get_value(
            "WAFD Hotel", {"hotel_name": hotel_name}, "name"
        )

        doc = (
            frappe.get_doc("WAFD Hotel", existing)
            if existing
            else frappe.new_doc("WAFD Hotel")
        )
        if not existing:
            doc.hotel_name = hotel_name
            doc.status = _safe_select(meta, "status", DEFAULT_STATUS, DEFAULT_STATUS)

        values = {
            "city": _clean(row.get("city")) or "المدينة المنورة",
            "district": _clean(row.get("district")),
            "zone_type": _safe_select(
                meta, "zone_type", row.get("zone_type"), DEFAULT_ZONE
            ),
            "central_map_number": map_no,
            "central_sector": _safe_select(
                meta, "central_sector", row.get("central_sector")
            ),
            "source_authority": _clean(row.get("source_authority")),
            "source_map_edition": _clean(row.get("source_map_edition")),
            # A map match is an official verification in the current DocType taxonomy.
            "verification_status": _safe_select(
                meta,
                "verification_status",
                MAP_VERIFICATION_STATUS,
                "يحتاج مراجعة / Needs Review",
            ),
            "source_notes": _clean(row.get("source_notes")),
            "last_verified_on": nowdate(),
        }

        for fieldname, value in values.items():
            if value not in (None, ""):
                doc.set(fieldname, value)

        if existing:
            doc.save(ignore_permissions=True)
        else:
            doc.insert(ignore_permissions=True)

