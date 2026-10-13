"""Install the simple Delivery Supervisor plan and common Madinah sites."""

import frappe


LOCATIONS = (
    ("المسجد النبوي", "The Prophet's Mosque", "مسجد أو حرم / Mosque or Haram", "https://www.google.com/maps/search/?api=1&query=The+Prophet%27s+Mosque+Madinah"),
    ("مسجد قباء", "Quba Mosque", "مسجد أو حرم / Mosque or Haram", "https://www.google.com/maps/search/?api=1&query=Quba+Mosque+Madinah"),
    ("مسجد القبلتين", "Al Qiblatain Mosque", "مسجد أو حرم / Mosque or Haram", "https://www.google.com/maps/search/?api=1&query=Al+Qiblatain+Mosque+Madinah"),
    ("مسجد الميقات", "Miqat Mosque", "مسجد أو حرم / Mosque or Haram", "https://www.google.com/maps/search/?api=1&query=Miqat+Mosque+Madinah"),
)


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_location", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_trip", force=True)
    frappe.reload_doc("wafd_one", "doctype", "wafd_delivery_proof", force=True)
    for page in ("wafd_role_home", "wafd_delivery_supervisor", "wafd_driver_trips"):
        frappe.reload_doc("wafd_one", "page", page, force=True)

    for name_ar, name_en, location_type, map_url in LOCATIONS:
        if frappe.db.exists("WAFD Delivery Location", {"location_name_ar": name_ar}):
            continue
        frappe.get_doc({
            "doctype": "WAFD Delivery Location",
            "location_name_ar": name_ar,
            "location_name_en": name_en,
            "location_type": location_type,
            "map_url": map_url,
            "status": "نشط / Active",
        }).insert(ignore_permissions=True)

    frappe.clear_cache(doctype="WAFD Delivery Location")
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="WAFD Delivery Proof")
    frappe.clear_cache(doctype="Page")
