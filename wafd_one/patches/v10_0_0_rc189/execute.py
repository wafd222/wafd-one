"""RC189: make undertaking PDF images self-contained and re-apply approval assets."""
import frappe

def execute():
    if not frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        return
    from wafd_one.patches.v10_0_0_rc188.execute import _repair_document_studio_template, _backfill_existing_undertakings
    _repair_document_studio_template()
    _backfill_existing_undertakings()
    # Clear compiled HTML one more time so every site uses the repaired canvas.
    if frappe.db.exists("DocType", "WAFD Document Template"):
        frappe.db.sql("""update `tabWAFD Document Template` set compiled_html='' where reference_doctype=%s""", ("WAFD Hotel Undertaking",))
    frappe.clear_cache(doctype="WAFD Hotel Undertaking")
