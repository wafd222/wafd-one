"""RC122: force-sync Iftar Print Formats so Preview, Full Page and PDF use one template.

The previous release relied on model sync alone. Existing database Print Format
records can retain older HTML, which explains a PDF containing legacy signature
markup even though the app JSON was already corrected. This patch updates only
fields that exist in the site's Frappe v16 schema and avoids optional columns.
"""

import json
from pathlib import Path
import frappe

PRINT_FORMAT_DIRS = (
    "wafd_iftar_daily_handover",
    "wafd_iftar_supervisor_receipt",
    "wafd_iftar_project_summary",
)


def _payload(folder):
    path = Path(frappe.get_app_path("wafd_one", "wafd_one", "print_format", folder, f"{folder}.json"))
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _existing_fields():
    meta = frappe.get_meta("Print Format")
    fields = {df.fieldname for df in meta.fields}
    # Core columns that are not represented as regular DocFields.
    fields.update({"name", "doc_type", "module", "standard", "custom_format", "print_format_type", "html", "disabled"})
    return fields


def _sync_one(data, fields):
    name = data["name"]
    desired_keys = (
        "doc_type", "module", "standard", "custom_format", "print_format_type",
        "html", "disabled", "show_section_headings", "line_breaks", "font",
        "default_print_language", "letter_head", "align_labels_right", "css",
        "margin_top", "margin_bottom", "margin_left", "margin_right",
    )
    values = {key: data.get(key) for key in desired_keys if key in fields and key in data}

    if frappe.db.exists("Print Format", name):
        # Database-level update deliberately bypasses stale Select validation and
        # optional v16 columns while replacing the exact HTML used by PDF.
        frappe.db.set_value("Print Format", name, values, update_modified=False)
    else:
        insert_values = {key: value for key, value in values.items() if key in fields}
        insert_values.update({"doctype": "Print Format", "name": name})
        frappe.get_doc(insert_values).insert(ignore_permissions=True)


def execute():
    if not frappe.db.exists("DocType", "Print Format"):
        return
    fields = _existing_fields()
    for folder in PRINT_FORMAT_DIRS:
        _sync_one(_payload(folder), fields)
    frappe.clear_cache(doctype="Print Format")
    frappe.clear_cache()
