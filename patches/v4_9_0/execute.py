from __future__ import annotations

import frappe


OFFICIAL_SOURCES = (
    {
        "source_name": "وزارة السياحة - لوائح ومعايير مرافق الضيافة",
        "source_category": "فنادق / Hotels",
        "authority": "وزارة السياحة السعودية",
        "source_url": "https://mt.gov.sa/",
        "verification_status": "مصدر رسمي جزئي / Partial Official Source",
        "notes": "مرجع رسمي للترخيص والتصنيف. لا يمثل قائمة عامة مكتملة ومفتوحة لجميع فنادق المدينة المنورة.",
    },
    {
        "source_name": "مكاتب شؤون الحج لحجاج الخارج 1445",
        "source_category": "بعثات حج / Hajj Missions",
        "authority": "وزارة الحج والعمرة",
        "source_url": "https://haj.gov.sa/ar/Open-Data/Hajj-affairs-offices-for-foreign-pilgrims-1445",
        "verification_status": "رسمي موثق / Official Verified",
        "notes": "بيانات مفتوحة رسمية لمكاتب شؤون الحجاج لحجاج الخارج لموسم 1445هـ.",
    },
    {
        "source_name": "دليل المعايير التغذوية للأغذية المقدمة في المنشآت الحكومية",
        "source_category": "وصفات وتغذية / Recipes & Nutrition",
        "authority": "الهيئة العامة للغذاء والدواء",
        "source_url": "https://www.sfda.gov.sa/sites/default/files/2023-08/Sfda2dde.pdf",
        "verification_status": "رسمي موثق / Official Verified",
        "notes": "مرجع للمعايير التغذوية وسلامة قوائم الوجبات، وليس كتاب وصفات شامل.",
    },
    {
        "source_name": "الدليل الإرشادي للإفصاح عن السعرات الحرارية",
        "source_category": "وصفات وتغذية / Recipes & Nutrition",
        "authority": "الهيئة العامة للغذاء والدواء",
        "source_url": "https://www.sfda.gov.sa/ar/regulations/3523355",
        "verification_status": "رسمي موثق / Official Verified",
        "notes": "مرجع رسمي للإفصاح عن السعرات في قوائم الطعام.",
    },
    {
        "source_name": "WAFD ONE - بيانات تشغيلية داخلية",
        "source_category": "تشغيل داخلي / Internal Operations",
        "authority": "شركة وفد المدينة لخدمات الإعاشة",
        "verification_status": "تشغيلي داخلي / Internal Operational",
        "notes": "الفنادق والوصفات والمكونات التشغيلية التي لم تتوفر لها بيانات رسمية عامة مكتملة تبقى موسومة كمعلومات تشغيلية تحتاج تحققًا دوريًا.",
    },
)


def _ensure_sources():
    for values in OFFICIAL_SOURCES:
        if not frappe.db.exists("WAFD Data Source", values["source_name"]):
            frappe.get_doc({"doctype": "WAFD Data Source", "status": "نشط / Active", **values}).insert(ignore_permissions=True)


def _mark_existing_records():
    today = frappe.utils.today()
    # Existing hotel list is useful operationally but cannot be represented as a
    # complete official register without an official licensed-facility export.
    frappe.db.sql("""
        update `tabWAFD Hotel`
        set source_authority = coalesce(nullif(source_authority, ''), 'شركة وفد المدينة لخدمات الإعاشة'),
            verification_status = coalesce(nullif(verification_status, ''), 'يحتاج مراجعة / Needs Review'),
            zone_type = case
                when district like '%%المركزية%%' then 'المنطقة المركزية / Central Zone'
                when district is not null and district != '' then 'خارج المنطقة المركزية / Outside Central Zone'
                else 'غير محدد / Unspecified' end
    """)
    frappe.db.sql("""
        update `tabWAFD Mission`
        set official_name = coalesce(nullif(official_name, ''), mission_name),
            mission_type = coalesce(nullif(mission_type, ''), 'مكتب شؤون حجاج / Hajj Affairs Office'),
            hajj_season = coalesce(nullif(hajj_season, ''), '1445 هـ'),
            source_authority = coalesce(nullif(source_authority, ''), 'وزارة الحج والعمرة'),
            source_url = coalesce(nullif(source_url, ''), 'https://haj.gov.sa/ar/Open-Data/Hajj-affairs-offices-for-foreign-pilgrims-1445'),
            verification_status = coalesce(nullif(verification_status, ''), 'يحتاج مراجعة / Needs Review')
    """)
    frappe.db.sql("""
        update `tabWAFD Recipe`
        set source_authority = coalesce(nullif(source_authority, ''), 'شركة وفد المدينة لخدمات الإعاشة'),
            verification_status = coalesce(nullif(verification_status, ''), 'تشغيلي داخلي / Internal Operational'),
            food_safety_notes = coalesce(nullif(food_safety_notes, ''), 'تطبق اشتراطات سلامة الغذاء المعتمدة ويجب التحقق من الحساسية ودرجات الحفظ قبل الإنتاج.')
    """)
    frappe.db.sql("""
        update `tabWAFD Ingredient`
        set source_authority = coalesce(nullif(source_authority, ''), 'شركة وفد المدينة لخدمات الإعاشة'),
            verification_status = coalesce(nullif(verification_status, ''), 'تشغيلي داخلي / Internal Operational')
    """)


def execute():
    frappe.reload_doc('wafd_one', 'doctype', 'wafd_data_source', force=True, reset_permissions=True)
    for name in ('wafd_hotel', 'wafd_mission', 'wafd_recipe', 'wafd_ingredient', 'wafd_stock_balance'):
        frappe.reload_doc('wafd_one', 'doctype', name, force=True, reset_permissions=True)
    _ensure_sources()
    _mark_existing_records()
    frappe.clear_cache()
