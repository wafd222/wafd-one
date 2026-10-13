import json

import frappe
from jinja2 import Environment, TemplateSyntaxError

from wafd_one.document_studio import compile_template
from wafd_one.patches.v10_0_0_rc38.execute import (
    LEGACY_UNDERTAKING_HTML,
    LOGO,
    invoice_canvas,
    undertaking_canvas,
)


def _validate_jinja(source, label):
    try:
        Environment().parse(source or "")
    except TemplateSyntaxError as exc:
        frappe.throw(f"{label}: Jinja syntax error at line {exc.lineno}: {exc.message}")


def _sync_document_studio_templates():
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return
    mapping = {
        "Invoice": invoice_canvas(),
        "Hotel Undertaking": undertaking_canvas(),
    }
    for category, canvas in mapping.items():
        names = frappe.get_all(
            "WAFD Document Template",
            filters={"document_category": category},
            pluck="name",
        )
        for name in names:
            doc = frappe.get_doc("WAFD Document Template", name)
            doc.logo = LOGO
            doc.page_size = "A4"
            doc.orientation = "Portrait"
            doc.direction = "RTL"
            doc.margin_top_mm = 0
            doc.margin_right_mm = 0
            doc.margin_bottom_mm = 0
            doc.margin_left_mm = 0
            doc.canvas_json = json.dumps(canvas, ensure_ascii=False)
            compiled = compile_template(doc)
            _validate_jinja(compiled, f"Document template {name}")
            doc.compiled_html = compiled
            doc.enabled = 1
            doc.is_default = 1
            doc.save(ignore_permissions=True)
    frappe.clear_cache(doctype="WAFD Document Template")


def _sync_undertaking_print_formats():
    if not frappe.db.exists("DocType", "Print Format"):
        return
    _validate_jinja(LEGACY_UNDERTAKING_HTML, "Hotel undertaking print format")
    names = frappe.get_all(
        "Print Format",
        filters={"doc_type": "WAFD Hotel Undertaking"},
        pluck="name",
    )
    for name in names:
        frappe.db.set_value(
            "Print Format",
            name,
            {
                "html": LEGACY_UNDERTAKING_HTML,
                "custom_format": 1,
                "print_format_type": "Jinja",
                "disabled": 0,
            },
            update_modified=False,
        )
    frappe.clear_cache(doctype="Print Format")


def execute():
    _sync_document_studio_templates()
    _sync_undertaking_print_formats()
