"""RC188 undertaking mobile actions, share/save support and signature repair."""
from __future__ import annotations

import json
import frappe
from frappe.utils import cint

TARGET = "WAFD Hotel Undertaking"


def _repair_document_studio_template():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    rows = frappe.get_all(
        "WAFD Document Template",
        filters={"reference_doctype": TARGET},
        fields=["name", "canvas_json", "signature", "stamp"],
    )
    settings = frappe.get_single("WAFD Print Settings") if frappe.db.exists("DocType", "WAFD Print Settings") else None
    for row in rows:
        doc = frappe.get_doc("WAFD Document Template", row.name)
        try:
            canvas = json.loads(doc.canvas_json or "{}")
        except Exception:
            continue
        changed = False
        for block in canvas.get("blocks") or []:
            kind = str(block.get("type") or "").lower()
            ident = str(block.get("id") or "").lower()
            if kind == "signature" or ident == "signature":
                src = '{{ doc.signature_image if doc.include_signature else "" }}'
                if block.get("src") != src:
                    block["src"] = src
                    # Preserve the approved position, size and all visual styling.
                    if kind not in {"signature", "image", "logo", "stamp"}:
                        block["type"] = "signature"
                    changed = True
            elif kind == "stamp" or ident == "stamp":
                src = '{{ doc.company_stamp if doc.include_stamp else "" }}'
                if block.get("src") != src:
                    block["src"] = src
                    if kind not in {"signature", "image", "logo", "stamp"}:
                        block["type"] = "stamp"
                    changed = True
        if settings:
            if settings.default_signature and doc.signature != settings.default_signature:
                doc.signature = settings.default_signature
                changed = True
            if settings.default_stamp and doc.stamp != settings.default_stamp:
                doc.stamp = settings.default_stamp
                changed = True
        if changed:
            doc.canvas_json = json.dumps(canvas, ensure_ascii=False)
            doc.compiled_html = ""  # force recompilation using the repaired dynamic assets
            doc.save(ignore_permissions=True)


def _backfill_existing_undertakings():
    if not frappe.db.exists("DocType", TARGET) or not frappe.db.exists("DocType", "WAFD Print Settings"):
        return
    settings = frappe.get_single("WAFD Print Settings")
    default_signature = settings.default_signature or ""
    default_stamp = settings.default_stamp or ""
    rows = frappe.get_all(TARGET, fields=["name", "signature_image", "company_stamp", "include_signature", "include_stamp"])
    for row in rows:
        values = {}
        if not row.signature_image and default_signature:
            values["signature_image"] = default_signature
        if not row.company_stamp and default_stamp:
            values["company_stamp"] = default_stamp
        if row.include_signature is None:
            values["include_signature"] = 1
        if row.include_stamp is None:
            values["include_stamp"] = 1
        if values:
            frappe.db.set_value(TARGET, row.name, values, update_modified=False)


def execute():
    if frappe.db.exists("DocType", TARGET):
        frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True, reset_permissions=True)
    _repair_document_studio_template()
    _backfill_existing_undertakings()
    # Synchronize the standard Frappe print format as a safe fallback without
    # changing the approved Document Studio layout.
    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()
    frappe.clear_cache(doctype=TARGET)
