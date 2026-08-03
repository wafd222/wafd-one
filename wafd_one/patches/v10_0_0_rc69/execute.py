import json
import frappe

from wafd_one.patches.v10_0_0_rc38.execute import invoice_canvas

LOGO = "/assets/wafd_one/images/wafd-almadinah-official.png"


def execute():
    """Refresh every invoice document template with the approved WAFD header.

    The layout intentionally matches the hotel undertaking: company/contact details
    at the upper-left, company identity in the middle, and the logo at the upper-right.
    """
    if not frappe.db.exists("DocType", "WAFD Document Template"):
        return

    names = frappe.get_all(
        "WAFD Document Template",
        filters={"document_category": "Invoice"},
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
        doc.canvas_json = json.dumps(invoice_canvas(), ensure_ascii=False)
        doc.save(ignore_permissions=True)

    frappe.clear_cache(doctype="WAFD Document Template")
