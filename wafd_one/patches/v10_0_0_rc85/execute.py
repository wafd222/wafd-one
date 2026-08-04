import frappe

CORRECT_NAME = "نزار بن نذير بن ظفر"

def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_hotel_undertaking", force=True, reset_permissions=True)
    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        wrong_names = ("نزار نذير بن ظفر", "نزار بن مذير بن ظفر", "نزار مذير بن ظفر", "نزار بن نذير ظفر", "نزار نذير ظفر")
        placeholders = ",".join(["%s"] * len(wrong_names))
        frappe.db.sql(f"""update `tabWAFD Hotel Undertaking` set authorized_signatory=%s where ifnull(authorized_signatory,'')='' or authorized_signatory in ({placeholders})""", (CORRECT_NAME, *wrong_names))
        frappe.db.sql(f"""update `tabWAFD Hotel Undertaking` set company_representative=%s where ifnull(company_representative,'')='' or company_representative in ({placeholders})""", (CORRECT_NAME, *wrong_names))
    from wafd_one.setup import ensure_hotel_undertaking_print_format
    ensure_hotel_undertaking_print_format()
    if frappe.db.exists("DocType", "WAFD Document Template"):
        from wafd_one.undertaking_template import UNDERTAKING_HTML
        names = frappe.get_all("WAFD Document Template", filters={"reference_doctype":"WAFD Hotel Undertaking"}, pluck="name")
        for name in names:
            frappe.db.set_value("WAFD Document Template", name, {"compiled_html":UNDERTAKING_HTML,"page_size":"A4","orientation":"Portrait","direction":"RTL","margin_top_mm":0,"margin_right_mm":0,"margin_bottom_mm":0,"margin_left_mm":0,"enabled":1,"is_default":0}, update_modified=False)
        if names:
            frappe.db.set_value("WAFD Document Template", names[0], "is_default", 1, update_modified=False)
    frappe.clear_cache(doctype="WAFD Hotel Undertaking")
    frappe.clear_cache(doctype="WAFD Document Template")
    frappe.clear_cache(doctype="Print Format")
