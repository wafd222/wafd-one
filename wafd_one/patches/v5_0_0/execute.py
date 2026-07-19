import frappe

DEFAULT_MEALS="إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner"

def execute():
    if frappe.db.exists("DocType", "WAFD Hotel Undertaking"):
        frappe.db.sql("""update `tabWAFD Hotel Undertaking` set meal_types=%s where coalesce(meal_types,'')='' and docstatus=0""", DEFAULT_MEALS)
        frappe.db.sql("""update `tabWAFD Hotel Undertaking` set company_logo=%s where coalesce(company_logo,'')=''""", "/assets/wafd_one/images/wafd-almadinah-official.png")
    frappe.clear_cache()
