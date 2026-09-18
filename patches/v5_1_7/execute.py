import json
from pathlib import Path

import frappe


def execute():
    source = (
        Path(__file__).resolve().parents[2]
        / "wafd_one"
        / "print_format"
        / "wafd_hotel_undertaking"
        / "wafd_hotel_undertaking.json"
    )
    if not source.exists():
        frappe.throw(f"Print format source not found: {source}")

    data = json.loads(source.read_text(encoding="utf-8"))
    name = data.get("name", "تعهد والتزام إعاشة — WAFD")

    if frappe.db.exists("Print Format", name):
        doc = frappe.get_doc("Print Format", name)
        doc.html = data.get("html", "")
        doc.custom_format = 1
        doc.print_format_type = data.get("print_format_type", "Jinja")
        doc.disabled = 0
        doc.raw_printing = 0
        doc.save(ignore_permissions=True)
    else:
        frappe.get_doc(data).insert(ignore_permissions=True)

    if frappe.db.exists("DocType", "WAFD Print Settings"):
        settings = frappe.get_single("WAFD Print Settings")
        settings.show_company_details = 0
        settings.header_line_width = 0
        settings.margin_top = 5
        settings.margin_bottom = 15
        settings.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache(doctype="Print Format")
