"""RC343 restore undertaking assets, visibility, and compact mobile navigation."""
import frappe


TARGET = "WAFD Hotel Undertaking"


def execute():
    if not frappe.db.exists("DocType", TARGET):
        return
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True, reset_permissions=True)

    # Re-run the current resolver for every historical record. It can recover
    # from Print Settings, Document Studio, an earlier approved undertaking,
    # or a clearly named company asset.
    for name in frappe.get_all(TARGET, pluck="name"):
        doc = frappe.get_doc(TARGET, name)
        before_signature = doc.signature_image or ""
        before_stamp = doc.company_stamp or ""
        doc._fill_company_approval_assets()
        values = {"include_signature": 1, "include_stamp": 1}
        if doc.signature_image and doc.signature_image != before_signature:
            values["signature_image"] = doc.signature_image
        if doc.company_stamp and doc.company_stamp != before_stamp:
            values["company_stamp"] = doc.company_stamp
        frappe.db.set_value(TARGET, name, values, update_modified=False)

    if frappe.db.exists("DocType", "WAFD Document Template"):
        frappe.db.sql(
            "update `tabWAFD Document Template` set compiled_html='' where reference_doctype=%s",
            (TARGET,),
        )
    frappe.clear_cache(doctype=TARGET)
    frappe.clear_cache()
