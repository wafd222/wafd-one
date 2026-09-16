from __future__ import annotations

import csv
from pathlib import Path

import frappe
from frappe.utils import nowdate


def _load_rows(filename):
    path = Path(frappe.get_app_path("wafd_one")) / "reference_data" / filename
    if not path.exists():
        frappe.log_error(
            title="WAFD ONE RC225 hotel bilingual data",
            message=f"Missing optional reference file: {path}",
        )
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _update_exact_name(row):
    hotel_name = (row.get("hotel_name") or "").strip()
    if not hotel_name:
        return False
    existing = frappe.db.get_value("WAFD Hotel", {"hotel_name": hotel_name}, "name")
    if not existing:
        return False

    doc = frappe.get_doc("WAFD Hotel", existing)
    changed = False
    for fieldname in ("hotel_name_ar", "hotel_name_en"):
        value = (row.get(fieldname) or "").strip()
        if value and doc.get(fieldname) != value:
            doc.set(fieldname, value)
            changed = True

    if changed:
        note = (row.get("bilingual_name_method") or "").strip()
        if note:
            existing_notes = (doc.source_notes or "").strip()
            marker = f"RC225 bilingual name review: {note}"
            if marker not in existing_notes:
                doc.source_notes = (existing_notes + "\n" + marker).strip()
        doc.last_verified_on = nowdate()
        doc.save(ignore_permissions=True)
    return changed


def execute():
    if not frappe.db.exists("DocType", "WAFD Hotel"):
        return

    # Sync the new Arabic-name field before writing values.
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel", force=True)

    updated = 0
    reviewed = 0
    for filename in (
        "madinah_hotels_400_ota_review.csv",
        "madinah_central_and_nearby_hotels_2026.csv",
    ):
        for row in _load_rows(filename):
            reviewed += 1
            if _update_exact_name(row):
                updated += 1

    # New records created from the undertaking screen require Arabic + English
    # names, while the catalogue remains searchable in either language.
    frappe.clear_cache(doctype="WAFD Hotel")
    frappe.clear_cache()

    frappe.logger("wafd_one").info(
        "RC225 bilingual hotel catalogue reviewed=%s updated=%s", reviewed, updated
    )
