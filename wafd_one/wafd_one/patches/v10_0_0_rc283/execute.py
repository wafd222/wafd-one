"""Correct known hotel Arabic names while retaining stable document identifiers."""

import frappe


HOTEL_CORRECTIONS = {
    "WAFD-HOTEL-makarem-burj-al-madinah-83e62": "أجنحة مكارم برج المدينة",
    "WAFD-HOTEL-intercontinental-dar-al-iman-7d1f5": "إنتركونتيننتال المدينة - دار الإيمان",
    "WAFD-HOTEL-nozol-snabel-al-madinah-980c5": "نزل سنابل المدينة",
    "WAFD-HOTEL-alritz-al-madinah-hotel-14b47": "فندق الريتز المدينة",
    "WAFD-HOTEL-al-aqeeq-madinah-hotel-8acf3": "فندق العقيق المدينة (سابقًا ميلينيوم)",
    "WAFD-HOTEL-al-safa-al-barakah-e3af2": "الصفا البركة",
    "WAFD-HOTEL-frontel-al-harithia-hotel-2c46f": "فندق فرونتيل الحارثية (سابقًا مجلس جراند)",
    "WAFD-HOTEL-burj-mawaddah-hotel-7e264": "فندق برج مودة",
    "WAFD-HOTEL-astoneast-taiba-hotel-47fdb": "فندق أستون إيست طيبة (سابقًا أرتال العالمي)",
    "WAFD-HOTEL-al-muna-kareem-hotel-a5254": "فندق المنى كريم (سابقًا ليدر)",
    "WAFD-HOTEL-afaq-al-salam-al-thahabi-hotel-36fbe": "فندق آفاق السلام الذهبي (سابقًا رياض المدينة)",
}

OLD_ARABIC = {
    "الصفا ال باراكاه": "الصفا البركة",
    "الصفا ال باراكه": "الصفا البركة",
    "الصفا آل باراكاه": "الصفا البركة",
    "الصفا آل بركة": "الصفا البركة",
    "فندق افاق السلام الذهبي ريياده المدينه": "فندق آفاق السلام الذهبي (سابقًا رياض المدينة)",
    "فندق افاك السلام الذهبي بكس ريياده المدينه": "فندق آفاق السلام الذهبي (سابقًا رياض المدينة)",
    "فندق افاق السلام الذهبي رياده المدينه": "فندق آفاق السلام الذهبي (سابقًا رياض المدينة)",
    "فندق افاق السلام الذهبي": "فندق آفاق السلام الذهبي",
    "فندق افاك": "فندق آفاق",
    "فندق افاق": "فندق آفاق",
}


def execute():
    for name, corrected in HOTEL_CORRECTIONS.items():
        if frappe.db.exists("WAFD Hotel", name):
            frappe.db.set_value("WAFD Hotel", name, "hotel_name_ar", corrected, update_modified=False)
            for trip in frappe.get_all("WAFD Delivery Trip", filters={"hotel": name}, pluck="name"):
                frappe.db.set_value("WAFD Delivery Trip", trip, "destination_name", corrected, update_modified=False)
    for old, corrected in OLD_ARABIC.items():
        frappe.db.sql("update `tabWAFD Hotel` set hotel_name_ar=%s where hotel_name_ar=%s", (corrected, old))
        frappe.db.sql("update `tabWAFD Delivery Trip` set destination_name=%s where destination_name=%s", (corrected, old))
    frappe.reload_doc("wafd_one", "page", "wafd_delivery_supervisor", force=True)
    frappe.clear_cache()
