import frappe

def execute():
    # Remove stale custom-property overrides so shipped DocType metadata wins.
    for fieldname in ("advance_percent", "advance_amount", "default_source_warehouse"):
        for name in frappe.get_all("Property Setter", filters={"doc_type": "WAFD Contract", "field_name": fieldname}, pluck="name"):
            frappe.delete_doc("Property Setter", name, ignore_permissions=True, force=True)
    frappe.clear_cache(doctype="WAFD Contract")
    frappe.clear_cache(doctype="WAFD Invoice")
    frappe.clear_cache(doctype="WAFD Mission")
