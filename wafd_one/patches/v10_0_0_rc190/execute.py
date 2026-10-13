"""RC190: final undertaking PDF image safety and legacy signature recovery."""
import frappe

TARGET = "WAFD Hotel Undertaking"

def execute():
    if not frappe.db.exists("DocType", TARGET):
        return
    signature = stamp = ""
    if frappe.db.exists("DocType", "WAFD Print Settings"):
        settings = frappe.get_single("WAFD Print Settings")
        signature = settings.default_signature or ""
        stamp = settings.default_stamp or ""
    if frappe.db.exists("DocType", "WAFD Document Template"):
        name = frappe.db.get_value("WAFD Document Template", {"reference_doctype": TARGET, "enabled": 1, "is_default": 1}, "name") or frappe.db.get_value("WAFD Document Template", {"reference_doctype": TARGET, "enabled": 1}, "name")
        if name:
            template = frappe.get_doc("WAFD Document Template", name)
            signature = signature or (template.signature or "")
            stamp = stamp or (template.stamp or "")
        frappe.db.sql("""update `tabWAFD Document Template` set compiled_html='' where reference_doctype=%s""", (TARGET,))
    rows = frappe.get_all(TARGET, fields=["name", "signature_image", "company_stamp", "include_signature", "include_stamp"])
    for row in rows:
        values = {}
        if not row.signature_image and signature:
            values["signature_image"] = signature
        if not row.company_stamp and stamp:
            values["company_stamp"] = stamp
        if row.include_signature is None:
            values["include_signature"] = 1
        if row.include_stamp is None:
            values["include_stamp"] = 1
        if values:
            frappe.db.set_value(TARGET, row.name, values, update_modified=False)
    frappe.clear_cache(doctype=TARGET)
