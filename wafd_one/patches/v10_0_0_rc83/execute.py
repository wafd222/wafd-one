import json
from pathlib import Path

import frappe


def execute():
    source = (
        Path(__file__).resolve().parents[2]
        / "wafd_one" / "print_format" / "wafd_hotel_undertaking"
        / "wafd_hotel_undertaking.json"
    )
    data = json.loads(source.read_text(encoding="utf-8"))
    html = data.get("html") or ""

    if frappe.db.exists("DocType", "Print Format"):
        names = set(frappe.get_all(
            "Print Format",
            filters={"doc_type": "WAFD Hotel Undertaking"},
            pluck="name",
        ))
        names.add(data["name"])
        for name in names:
            if frappe.db.exists("Print Format", name):
                frappe.db.set_value("Print Format", name, {
                    "html": html,
                    "doc_type": "WAFD Hotel Undertaking",
                    "custom_format": 1,
                    "print_format_type": "Jinja",
                    "disabled": 0,
                    "raw_printing": 0,
                }, update_modified=False)
            elif name == data["name"]:
                frappe.get_doc(data).insert(ignore_permissions=True)

    if frappe.db.exists("DocType", "WAFD Document Template"):
        for name in frappe.get_all(
            "WAFD Document Template",
            filters={"reference_doctype": "WAFD Hotel Undertaking"},
            pluck="name",
        ):
            frappe.db.set_value(
                "WAFD Document Template", name,
                {"compiled_html": html, "enabled": 1},
                update_modified=False,
            )

    frappe.clear_cache(doctype="Print Format")
    if frappe.db.exists("DocType", "WAFD Document Template"):
        frappe.clear_cache(doctype="WAFD Document Template")
