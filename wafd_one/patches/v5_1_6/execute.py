import json
from pathlib import Path

import frappe


def execute():
    source = Path(__file__).resolve().parents[2] / "wafd_one" / "print_format" / "wafd_hotel_undertaking" / "wafd_hotel_undertaking.json"
    if not source.exists():
        return
    data = json.loads(source.read_text(encoding="utf-8"))
    name = data.get("name", "WAFD Hotel Undertaking")
    if frappe.db.exists("Print Format", name):
        doc = frappe.get_doc("Print Format", name)
        doc.html = data.get("html", "")
        doc.custom_format = 1
        doc.print_format_type = data.get("print_format_type", "Jinja")
        doc.disabled = 0
        doc.save(ignore_permissions=True)
    else:
        frappe.get_doc(data).insert(ignore_permissions=True)
    settings = frappe.get_single("WAFD Print Settings") if frappe.db.exists("DocType", "WAFD Print Settings") else None
    if settings:
        settings.show_company_details = 0
        settings.header_line_width = 0
        settings.save(ignore_permissions=True)
    frappe.clear_cache(doctype="Print Format")
