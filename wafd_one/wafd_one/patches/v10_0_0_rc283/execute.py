"""Correct visible hotel names and refresh delivery pages without losing history."""

import frappe


HOTEL_CORRECTIONS = {
    "makarem burj al madinah hotel and suites": ("أجنحة مكارم برج المدينة", "Makarem Burj Al Madinah Hotel and Suites"),
    "intercontinental madinah - dar al iman by ihg": ("إنتركونتيننتال المدينة - دار الإيمان", "Intercontinental Madinah - Dar Al Iman by IHG"),
    "nozol snabel almadinah": ("نزل سنابل المدينة", "Nozol Snabel Al Madinah"),
    "alritz almadinah hotel": ("فندق الريتز المدينة", "Al Ritz Al Madinah Hotel"),
    "al aqeeq hotel madinah ex. millennium": ("فندق العقيق المدينة (سابقًا ميلينيوم)", "Al Aqeeq Hotel Madinah ex. Millennium"),
    "al-safa-al-barakah": ("الصفا البركة", "Al Safa Al Barakah"),
    "frontel al harithia ex majlis grand": ("فندق فرونتيل الحارثية (سابقًا مجلس جراند)", "Frontel Al Harithia EX Majlis Grand"),
    "burj mawaddah hotel": ("فندق برج مودة", "Burj Mawaddah Hotel"),
    "astoneast taiba hotel ex artal al alami": ("فندق أستون إيست طيبة (سابقًا أرتال العالمي)", "Astoneast Taiba Hotel Ex Artal Al Alami"),
    "al muna kareem hotel- ex leader": ("فندق المنى كريم (سابقًا ليدر)", "Al Muna Kareem Hotel - Ex Leader"),
    "afaq al salam al zahabi hotel ex riyadh al madinah hotel": ("فندق آفاق السلام الذهبي (سابقًا رياض المدينة)", "Afaq Al Salam Al Zahabi Hotel Ex Riyadh Al Madinah Hotel"),
}

OLD_ARABIC = {
    "أجنحة مكارم بورج المدينة": "أجنحة مكارم برج المدينة",
    "إنتركونتيننتالمدينة دار الإيمان من آي إتش جي": "إنتركونتيننتال المدينة - دار الإيمان",
    "نزل سنابيل الماديناه": "نزل سنابل المدينة",
    "فندق الريتز الماديناه": "فندق الريتز المدينة",
    "فندق العقيق المدينة يكس ميلينيوم": "فندق العقيق المدينة (سابقًا ميلينيوم)",
    "الصفا ال باراكاه": "الصفا البركة",
    "فرونتيل الحارثية يكس ماجليس جراند": "فندق فرونتيل الحارثية (سابقًا مجلس جراند)",
    "فندق بورج مودة": "فندق برج مودة",
    "فندق أستون إيست طيبة يكس أرتال الامي": "فندق أستون إيست طيبة (سابقًا أرتال العالمي)",
    "فندق ال منى كريم يكس ليدير": "فندق المنى كريم (سابقًا ليدر)",
    "فندق افاك السلام الذهبي يكس ريياده المدينة": "فندق آفاق السلام الذهبي (سابقًا رياض المدينة)",
}


def execute():
    corrected_hotels = {}
    if frappe.db.exists("DocType", "WAFD Hotel"):
        for row in frappe.get_all(
            "WAFD Hotel",
            fields=["name", "hotel_name", "hotel_name_ar", "hotel_name_en"],
            limit_page_length=0,
        ):
            source_key = (row.hotel_name_en or row.hotel_name or "").strip().casefold()
            correction = HOTEL_CORRECTIONS.get(source_key)
            if not correction and row.hotel_name_ar in OLD_ARABIC:
                correction = (OLD_ARABIC[row.hotel_name_ar], row.hotel_name_en or row.hotel_name)
            if not correction:
                continue
            arabic_name, english_name = correction
            frappe.db.set_value(
                "WAFD Hotel", row.name,
                {"hotel_name_ar": arabic_name, "hotel_name_en": english_name},
                update_modified=False,
            )
            corrected_hotels[row.name] = (arabic_name, english_name)

    if frappe.db.exists("DocType", "WAFD Delivery Trip"):
        for hotel, (arabic_name, english_name) in corrected_hotels.items():
            frappe.db.sql(
                """update `tabWAFD Delivery Trip`
                   set destination_name=%s, destination_name_en=%s
                   where hotel=%s""",
                (arabic_name, english_name, hotel),
            )
        for old_name, arabic_name in OLD_ARABIC.items():
            frappe.db.sql(
                """update `tabWAFD Delivery Trip`
                   set destination_name=%s
                   where destination_name=%s""",
                (arabic_name, old_name),
            )

    frappe.reload_doc("wafd_one", "page", "wafd_delivery_supervisor", force=True)
    frappe.clear_cache(doctype="WAFD Hotel")
    frappe.clear_cache(doctype="WAFD Delivery Trip")
    frappe.clear_cache(doctype="Page")
    frappe.clear_cache()
