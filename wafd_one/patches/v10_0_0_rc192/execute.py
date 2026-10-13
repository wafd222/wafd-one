"""RC192: recover legacy undertaking approval assets and clear stale template HTML."""
import frappe

TARGET = "WAFD Hotel Undertaking"

def execute():
    if not frappe.db.exists("DocType", TARGET):
        return
    # Use the DocType's own resolver so old signatures can be recovered from
    # Print Settings, Document Studio or clearly-named File uploads.
    rows = frappe.get_all(TARGET, pluck="name")
    for name in rows:
        doc = frappe.get_doc(TARGET, name)
        before = (doc.signature_image or "", doc.company_stamp or "")
        doc._fill_company_approval_assets()
        values = {}
        if doc.signature_image and doc.signature_image != before[0]:
            values["signature_image"] = doc.signature_image
        if doc.company_stamp and doc.company_stamp != before[1]:
            values["company_stamp"] = doc.company_stamp
        if values:
            frappe.db.set_value(TARGET, name, values, update_modified=False)
    if frappe.db.exists("DocType", "WAFD Document Template"):
        frappe.db.sql("update `tabWAFD Document Template` set compiled_html='' where reference_doctype=%s", (TARGET,))
    frappe.clear_cache(doctype=TARGET)
