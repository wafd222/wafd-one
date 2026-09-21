from __future__ import annotations

import json

import frappe

from wafd_one.patches.v10_0_0_rc146.execute import (
    _certificate_canvas,
    _ensure_service_certificate_template,
)


def _single_page_certificate_canvas():
    """Keep the approved RC146 design while ensuring every block stays inside page 1."""
    canvas = _certificate_canvas()
    positions = {
        # RC146 footer ended at y=1048 while the renderer page is 1040px high.
        # wkhtmltopdf can therefore spill only the footer into a second page.
        "body": (70, 205, 655, 235),
        "info": (70, 465, 655, 145),
        "signature": (70, 710, 655, 135),
        "footer": (48, 965, 697, 38),
    }
    for block in canvas.get("blocks") or []:
        if block.get("id") in positions:
            x, y, w, h = positions[block["id"]]
            block.update({"x": x, "y": y, "w": w, "h": h})
    canvas["version"] = 5
    return canvas


def execute():
    template_name = _ensure_service_certificate_template()
    if not template_name:
        return

    # There must be exactly one default project template. RC146 could leave an
    # older legacy certificate/default row enabled, making PDF selection nondeterministic.
    frappe.db.sql(
        """update `tabWAFD Document Template`
           set is_default=0
         where reference_doctype=%s and name!=%s""",
        ("WAFD Catering Project", template_name),
    )

    doc = frappe.get_doc("WAFD Document Template", template_name)
    doc.is_default = 1
    doc.enabled = 1
    doc.canvas_json = json.dumps(_single_page_certificate_canvas(), ensure_ascii=False)
    doc.custom_css = (
        "html,body{margin:0!important;padding:0!important;}"
        ".wds-print-page{overflow:hidden!important;page-break-after:avoid!important;"
        "page-break-before:avoid!important;page-break-inside:avoid!important;}"
        ".wds-print-block{page-break-inside:avoid!important;}"
        "table,tr,td,th{page-break-inside:avoid!important;}"
    )
    doc.save(ignore_permissions=True)
    frappe.clear_cache()
