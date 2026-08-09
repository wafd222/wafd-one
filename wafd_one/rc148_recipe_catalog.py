"""RC148 recipe integrity and Hajj/visitor cuisine reference.

Dish names are backed, where possible, by official tourism/government food
references. Ingredient quantities are WAFD internal operational references for
100 portions; they are NOT represented as official-source recipe quantities.
"""
from __future__ import annotations

SOURCES = {
    "sfda_hajj": ("الهيئة العامة للغذاء والدواء السعودية (SFDA)", "https://www.sfda.gov.sa/ar/HajjAndOmrah"),
    "saudi": ("Visit Saudi — official tourism portal", "https://www.visitsaudi.com/content/dam/saudi-tourism/media/guides/saudi-series-culture-english.pdf"),
    "india": ("Incredible India — Ministry of Tourism", "https://www.prod.incredibleindia.gov.in/content/incredible-india-v2/en/destinations/delhi/food-and-cuisine.html"),
    "pakistan": ("Pakistan Tourism Development Corporation", "https://tourism.gov.pk/pakistan.html"),
    "pakistan_heritage": ("National Register of Intangible Cultural Heritage — Pakistan", "https://heritage.pakistan.gov.pk/SiteImage/Misc/files/ICH%20Pakistan%20Low.pdf"),
    "bangladesh": ("Bangladesh Tourism Board", "https://tourismboard.gov.bd/sites/default/files/files/tourismboard.portal.gov.bd/page/aa3dacc5_f200_47c7_8445_12aff09f9450/BTB%20Tourist%20Handbook%20%281%29.pdf"),
    "indonesia": ("Indonesia Travel — official tourism portal", "https://www.indonesia.travel/sa/ar/travel-ideas/gastronomy/the-ultimate-guide-to-must-try-indonesian-food"),
    "malaysia": ("Tourism Malaysia", "https://www.malaysia.travel/explore/malaysian-food-52-top-picks-you-shouldn-t-miss"),
    "uzbekistan": ("Uzbekistan Travel — official tourism portal", "https://uzbekistan.travel/en/c/uzbek-cuisine/"),
    "morocco": ("Moroccan National Tourist Office", "https://www.visitmorocco.com/en/travel-info/food-drinks"),
    "uae": ("Experience Abu Dhabi — official tourism portal", "https://visitabudhabi.ae/en/plan-your-trip/culture-and-traditions/emirati-cuisine"),
    "qatar": ("Visit Qatar — official tourism portal", "https://visitqatar.com/intl-en/about-qatar/cuisine"),
    "turkey": ("GoTürkiye — official tourism portal", "https://gastronomy.goturkiye.com/turkish-cuisine"),
    "srilanka": ("Sri Lanka Tourism", "https://srilanka.travel/food"),
    "jordan": ("Visit Jordan — official tourism portal", "https://edutravel.visitjordan.com/en/page/79/Food-and-Drinks"),
    "ethiopia": ("Explore Ethiopia — official tourism portal", "https://exploreethiopia.travel/"),
    "china": ("Xi'an Municipal Government — Dining", "https://en.xa.gov.cn/CultureTravel/Dining/1691691507897716737.html"),
    "nigeria": ("Peer-reviewed Nigerian cuisine overview / ScienceDirect", "https://www.sciencedirect.com/science/article/pii/S1878450X26001526"),
}


def _safe_data_url(url: str) -> str:
    """Return a URL that is safe for Frappe Data fields (max 140 chars).

    RC148 originally used one official Bangladesh Tourism Board PDF URL that
    is 161 characters long. WAFD Recipe.source_url is a Frappe Data field and
    therefore rejects values longer than 140 characters during pre-model-sync
    patches. Keep the exact deep-link in the review CSV, while the live master
    record stores the stable official site URL when a source URL is too long.
    """
    url = (url or "").strip()
    if len(url) <= 140:
        return url
    try:
        from urllib.parse import urlsplit

        parts = urlsplit(url)
        if parts.scheme and parts.netloc:
            root = f"{parts.scheme}://{parts.netloc}/"
            if len(root) <= 140:
                return root
    except Exception:
        pass
    return url[:140]


def spec(name, category, cuisine, nationalities, items, source_key=None, notes=""):
    authority, raw_url = SOURCES.get(source_key, ("WAFD ONE — operational reference", ""))
    url = _safe_data_url(raw_url)
    verification = (
        "يحتاج مراجعة / Needs Review" if source_key == "nigeria"
        else "تشغيلي داخلي / Internal Operational" if source_key in (None, "sfda_hajj")
        else "رسمي موثق / Official Verified"
    )
    return {
        "recipe_name": name,
        "meal_category": category,
        "cuisine": cuisine,
        "suitable_nationalities": nationalities,
        "items": items,
        "source_authority": authority,
        "source_url": url,
        "verification_status": verification,
        "last_verified_on": "2026-08-09" if source_key else "",
        "source_notes": (notes + " " if notes else "") + "اسم الطبق/النمط مرجعي؛ كميات 100 حصة هي معيار تشغيلي داخلي لـ WAFD وتحتاج اعتماد الشيف والبعثة قبل الإنتاج.",
    }


# Repair every recipe name that legacy patches could create without child ingredients.
REPAIR_RECIPES = [
    spec("أرز أوزبكي بلوف", "غداء / Lunch", "أوزبكي / Uzbek", "أوزبكستان، طاجيكستان، كازاخستان، قرغيزستان، تركمانستان", [("أرز بسمتي",18),("لحم بقري",24),("جزر",7),("بصل",5),("زيت نباتي",3),("كمون",0.35)], "uzbekistan"),
    spec("أرز وصلصة الفول السوداني", "غداء / Lunch", "غرب أفريقي / West African", "مالي، السنغال، موريتانيا، غينيا، ساحل العاج", [("أرز بسمتي",17),("لحم بقري",20),("زبدة فول سوداني",6),("طماطم",4),("بصل",4),("جزر",3)]),
    spec("أيام غورينغ", "غداء / Lunch", "إندونيسي / Indonesian", "إندونيسيا", [("دجاج كامل مبرد",45),("صلصة صويا",3),("ثوم",1),("زنجبيل",0.8),("زيت نباتي",2),("أرز ياسمين",17)], "indonesia"),
    spec("إفطار رمضان آسيوي", "إفطار رمضان / Ramadan Iftar", "آسيوي / Asian", "إندونيسيا، ماليزيا، سنغافورة، تايلاند، الفلبين", [("تمر سكري",2.5),("ماء 330 مل",100),("أرز ياسمين",14),("صدور دجاج",18),("خيار",4),("عصير 200 مل",100)]),
    spec("إفطار رمضان اقتصادي", "إفطار رمضان / Ramadan Iftar", "عام / General", "جميع البعثات", [("تمر سكري",2.5),("ماء 330 مل",100),("لبن",100),("خبز عربي",100),("منديل معطر",100),("علبة إفطار صائم",100)]),
    spec("إفطار رمضان عربي", "إفطار رمضان / Ramadan Iftar", "عربي / Arabic", "البعثات العربية", [("تمر سكري",2.5),("ماء 330 مل",100),("لبن",100),("حمص حب",8),("خبز عربي",120),("سمبوسة خضار",100)]),
    spec("إفطار رمضان فاخر", "إفطار رمضان / Ramadan Iftar", "عام / General", "جميع البعثات", [("تمر عجوة",2.5),("ماء 330 مل",100),("لبن",100),("سمبوسة لحم",100),("عصير برتقال 200 مل",100),("كيك فردي",100),("علبة إفطار صائم",100)]),
    spec("إفطار رمضان قياسي", "إفطار رمضان / Ramadan Iftar", "عام / General", "جميع البعثات", [("تمر سكري",2.5),("ماء 330 مل",100),("لبن",100),("سمبوسة خضار",100),("عصير 200 مل",100),("علبة إفطار صائم",100)]),
    spec("برياني لحم باكستاني", "غداء / Lunch", "باكستاني / Pakistani", "باكستان", [("أرز بسمتي",18),("لحم بقري",25),("زبادي",10),("بصل",5),("طماطم",4),("بهارات برياني",0.8),("زيت نباتي",2)], "pakistan"),
    spec("تشانا مسالا", "غداء / Lunch", "هندي / Indian", "الهند، باكستان", [("حمص حب",14),("طماطم",4),("بصل",4),("زنجبيل",0.7),("ثوم",0.7),("جارام ماسالا",0.5)], "india"),
    spec("ثيبودين", "غداء / Lunch", "سنغالي / Senegalese", "السنغال، موريتانيا", [("سمك فيليه",24),("أرز بسمتي",17),("ملفوف",5),("جزر",4),("معجون طماطم",3),("تمر هندي",1)]),
    spec("جولوف رايس", "غداء / Lunch", "غرب أفريقي / West African", "نيجيريا، غانا، السنغال، غينيا، ساحل العاج، الكاميرون", [("أرز بسمتي",18),("طماطم",7),("فلفل رومي",4),("بصل",5),("معجون طماطم",3),("فلفل حار",0.4),("زيت نباتي",2)], "nigeria"),
    spec("حليم", "عشاء / Dinner", "جنوب آسيوي / South Asian", "باكستان، بنغلاديش، الهند", [("لحم بقري",18),("برغل",6),("عدس أحمر",5),("حمص حب",4),("بصل",4),("زنجبيل",0.6)]),
    spec("حمص وفلافل", "إفطار / Breakfast", "شامي / Levantine", "الأردن، فلسطين، سوريا، لبنان والعامة", [("حمص حب",12),("دقيق حمص",8),("طحينة",4),("بقدونس",2),("بصل",3),("ثوم",0.7),("خبز عربي",120)], "jordan"),
    spec("خضار مشكلة وأرز", "غداء / Lunch", "عام / General", "جميع البعثات", [("أرز بسمتي",17),("بطاطس",6),("جزر",5),("كوسة",5),("فاصوليا خضراء",4),("بازلاء مجمدة",3),("زيت نباتي",2)]),
    spec("خيتشوري", "غداء / Lunch", "بنغلاديشي / Bangladeshi", "بنغلاديش", [("أرز بسمتي",14),("عدس أحمر",8),("بصل",4),("طماطم",3),("كركم",0.25),("زيت نباتي",2)], "bangladesh"),
    spec("دجاج بالكاري", "غداء / Lunch", "جنوب آسيوي / South Asian", "الهند، باكستان، بنغلاديش، سريلانكا", [("صدور دجاج",24),("بصل",4),("طماطم",4),("زنجبيل",1),("ثوم",1),("كاري بودرة",0.7),("زبادي",8)], "india"),
    spec("دجاج جولوف", "غداء / Lunch", "نيجيري / Nigerian", "نيجيريا، غانا، الكاميرون", [("دجاج كامل مبرد",42),("أرز بسمتي",18),("طماطم",7),("فلفل رومي",4),("بصل",5),("معجون طماطم",3),("فلفل حار",0.4)], "nigeria"),
    spec("دجاج مشوي وأرز", "غداء / Lunch", "عام / General", "جميع البعثات", [("أرز بسمتي",17),("دجاج كامل مبرد",50),("زبادي",15),("ثوم",1),("ليمون",3),("بهارات مشكلة",0.6)]),
    spec("روتي وخضار", "إفطار / Breakfast", "جنوب آسيوي / South Asian", "الهند، باكستان، بنغلاديش، نيبال", [("خبز شباتي",100),("بطاطس",8),("قرنبيط",6),("جزر",4),("بازلاء مجمدة",3),("بصل",3),("كاري بودرة",0.5)]),
    spec("ساتاي دجاج", "عشاء / Dinner", "جنوب شرق آسيوي / Southeast Asian", "إندونيسيا، ماليزيا", [("صدور دجاج",25),("فول سوداني",5),("حليب جوز الهند",4),("صلصة صويا",2),("ثوم",0.8),("أرز ياسمين",16)], "malaysia"),
    spec("ساندويتش تونة", "عشاء / Dinner", "عام / General", "جميع البعثات", [("خبز صامولي",100),("تونة معلبة",14),("مايونيز",4),("خيار",4),("مخلل",2)]),
    spec("ساندويتش جبن", "إفطار / Breakfast", "عام / General", "جميع البعثات", [("خبز صامولي",100),("جبنة شرائح",100),("خيار",4),("عصير 200 مل",100)]),
    spec("ساندويتش دجاج", "عشاء / Dinner", "عام / General", "جميع البعثات", [("خبز صامولي",100),("صدور دجاج",18),("مايونيز",4),("خس",4),("مخلل",2)]),
    spec("سحور آسيوي", "سحور / Suhoor", "آسيوي / Asian", "البعثات الآسيوية", [("أرز ياسمين",12),("بيض",100),("صدور دجاج",12),("خيار",4),("لبن",100),("ماء 330 مل",100)]),
    spec("سحور إندونيسي", "سحور / Suhoor", "إندونيسي / Indonesian", "إندونيسيا", [("أرز ياسمين",14),("صدور دجاج",14),("بيض",100),("صلصة صويا",2),("خيار",4),("ماء 330 مل",100)], "indonesia"),
    spec("سحور عربي", "سحور / Suhoor", "عربي / Arabic", "البعثات العربية", [("فول",12),("بيض",100),("لبنة",5),("خبز عربي",120),("لبن",100),("ماء 330 مل",100)]),
    spec("سحور متوازن", "سحور / Suhoor", "عام / General", "جميع البعثات", [("بيض",100),("جبنة شرائح",100),("خبز عربي",100),("موز",12),("لبن",100),("ماء 330 مل",100)]),
    spec("سحور هندي", "سحور / Suhoor", "هندي / Indian", "الهند", [("خبز شباتي",100),("بيض",100),("حمص حب",10),("زبادي",10),("شاي",300),("ماء 330 مل",100)], "india"),
    spec("سلطة فواكه", "وجبة خفيفة / Snack", "عام / General", "جميع البعثات", [("موز",8),("تفاح",8),("برتقال",8),("عنب أخضر",5),("مانجو",5)]),
    spec("سمك بالكاري البنغالي", "غداء / Lunch", "بنغلاديشي / Bangladeshi", "بنغلاديش", [("سمك فيليه",25),("بطاطس",8),("طماطم",4),("بصل",4),("كركم",0.25),("فلفل حار",0.5),("أرز بسمتي",16)], "bangladesh"),
    spec("سمك مشوي وأرز", "غداء / Lunch", "عام / General", "جميع البعثات", [("أرز بسمتي",17),("سمك فيليه",25),("زيت نباتي",2),("ليمون",3),("بهارات سمك",0.5)]),
    spec("شاورما دجاج", "عشاء / Dinner", "عربي / Arabic", "العرب، تركيا والعامة", [("صدور دجاج",22),("خبز عربي",100),("بهارات شاورما",0.5),("مايونيز",4),("بطاطس",12),("مخلل",3)]),
    spec("طاجن دجاج", "غداء / Lunch", "مغربي / Moroccan", "المغرب، الجزائر، تونس", [("دجاج كامل مبرد",45),("بصل",5),("طماطم",4),("ليمون",3),("زيت نباتي",2),("بهارات مشكلة",0.6)], "morocco"),
    spec("فول وبيض", "إفطار / Breakfast", "عربي / Arabic", "البعثات العربية والعامة", [("فول",14),("بيض",100),("طماطم",3),("بصل",2),("خبز عربي",120)]),
    spec("كبسة دجاج سعودية", "غداء / Lunch", "سعودي / Saudi", "السعودية، الخليج والعامة", [("أرز بسمتي",18),("دجاج كامل مبرد",50),("بصل",4),("طماطم",5),("بهارات كبسة",0.7),("زيت نباتي",3)], "saudi"),
    spec("كبسة لحم", "غداء / Lunch", "سعودي / Saudi", "السعودية، الخليج والعامة", [("أرز بسمتي",18),("لحم غنم",30),("بصل",4),("طماطم",4),("بهارات كبسة",0.7),("زيت نباتي",2)], "saudi"),
    spec("كسكس بالخضار واللحم", "غداء / Lunch", "مغاربي / Maghrebi", "المغرب، الجزائر، تونس، ليبيا، موريتانيا", [("كسكس",18),("لحم بقري",22),("جزر",5),("كوسة",5),("حمص حب",4),("طماطم",4),("بصل",3)], "morocco"),
    spec("كشري", "غداء / Lunch", "مصري / Egyptian", "مصر والعامة", [("أرز مصري",12),("مكرونة",6),("عدس أحمر",6),("حمص حب",4),("بصل",5),("معجون طماطم",4)]),
    spec("كفتة بالصلصة", "غداء / Lunch", "عربي / Arabic", "العرب، تركيا والعامة", [("لحم مفروم",22),("طماطم",5),("بصل",4),("بقدونس",1),("معجون طماطم",2),("بهارات مشكلة",0.5)]),
    spec("مانتي", "غداء / Lunch", "آسيا الوسطى / Central Asian", "أوزبكستان، تركيا، كازاخستان، قرغيزستان، طاجيكستان، تركمانستان", [("دقيق أبيض",14),("لحم مفروم",20),("بصل",6),("زبادي",8),("فلفل أسود",0.2)], "uzbekistan"),
    spec("مكرونة مبكبكة", "غداء / Lunch", "ليبي / Libyan", "ليبيا", [("مكرونة",16),("لحم بقري",20),("طماطم",5),("معجون طماطم",3),("بصل",4),("فلفل حار",0.4)]),
    spec("مندي لحم", "غداء / Lunch", "يمني / Yemeni", "اليمن، الخليج والعامة", [("أرز بسمتي",18),("لحم غنم",30),("بصل",4),("بهارات مندي",0.7),("هيل",0.08),("زيت نباتي",2)]),
    spec("ناسي ليماك", "إفطار / Breakfast", "ماليزي / Malaysian", "ماليزيا، سنغافورة", [("أرز ياسمين",16),("حليب جوز الهند",8),("بيض",100),("فول سوداني",4),("خيار",5),("فلفل حار",0.4)], "malaysia"),
]

# Common complete package formulas reused by the legacy Iftar/welcome recipe names.
_IFTAR_MOSQUE = [("لبن",100),("تمر سكري",2.5),("ماء 330 مل",100),("دقة مدينية",5000),("خبز عربي",100),("ملعقة بلاستيك",100),("منديل معطر",100),("علبة إفطار صائم",100)]
REPAIR_RECIPES += [
    spec("وجبة إفطار صائم المسجد النبوي", "إفطار رمضان / Ramadan Iftar", "مدني / Madinah", "جميع الجنسيات", list(_IFTAR_MOSQUE), "sfda_hajj", "مرجع تشغيل لإفطار صائم؛ لا يضيف الغلاف الخارجي الخاص بالمشاريع الخارجية."),
    spec("وجبة إفطار صائم مسجد قباء", "إفطار رمضان / Ramadan Iftar", "مدني / Madinah", "جميع الجنسيات", list(_IFTAR_MOSQUE), "sfda_hajj"),
    spec("وجبة إفطار صائم مسجد القبلتين", "إفطار رمضان / Ramadan Iftar", "مدني / Madinah", "جميع الجنسيات", list(_IFTAR_MOSQUE), "sfda_hajj"),
    spec("وجبة إفطار صائم ميقات ذي الحليفة", "إفطار رمضان / Ramadan Iftar", "مدني / Madinah", "جميع الجنسيات", list(_IFTAR_MOSQUE), "sfda_hajj"),
    spec("وجبة ترحيبية VIP", "وجبة ترحيبية / Welcome Meal", "عالمي / International", "جميع البعثات", [("أرز بسمتي",17),("دجاج كامل مبرد",45),("ماء 330 مل",100),("عصير برتقال 200 مل",100),("كيك فردي",100),("علبة وجبة رئيسية",100)]),
    spec("وجبة ترحيبية إفريقية", "وجبة ترحيبية / Welcome Meal", "إفريقي / African", "البعثات الإفريقية", [("أرز بسمتي",18),("دجاج كامل مبرد",42),("طماطم",5),("بصل",4),("ماء 330 مل",100),("علبة وجبة رئيسية",100)]),
    spec("وجبة ترحيبية إندونيسية", "وجبة ترحيبية / Welcome Meal", "إندونيسي / Indonesian", "إندونيسيا", [("أرز ياسمين",18),("صدور دجاج",20),("صلصة صويا",2),("خيار",4),("ماء 330 مل",100),("علبة وجبة رئيسية",100)], "indonesia"),
    spec("وجبة ترحيبية باكستانية", "وجبة ترحيبية / Welcome Meal", "باكستاني / Pakistani", "باكستان", [("أرز بسمتي",18),("دجاج كامل مبرد",42),("بهارات برياني",0.7),("زبادي",8),("ماء 330 مل",100),("علبة وجبة رئيسية",100)], "pakistan"),
    spec("وجبة ترحيبية عربية", "وجبة ترحيبية / Welcome Meal", "عربي / Arabic", "البعثات العربية", [("أرز بسمتي",18),("دجاج كامل مبرد",45),("حمص حب",5),("خبز عربي",100),("ماء 330 مل",100),("علبة وجبة رئيسية",100)]),
    spec("وجبة ترحيبية ماليزية", "وجبة ترحيبية / Welcome Meal", "ماليزي / Malaysian", "ماليزيا", [("أرز ياسمين",17),("صدور دجاج",20),("حليب جوز الهند",5),("فول سوداني",3),("ماء 330 مل",100),("علبة وجبة رئيسية",100)], "malaysia"),
    spec("وجبة ترحيبية هندية", "وجبة ترحيبية / Welcome Meal", "هندي / Indian", "الهند", [("أرز بسمتي",18),("صدور دجاج",22),("كاري بودرة",0.6),("زبادي",8),("ماء 330 مل",100),("علبة وجبة رئيسية",100)], "india"),
]

# Additional trusted-source dish names to broaden the reference library.
VERIFIED_RECIPES = [
    spec("سليق دجاج حجازي", "غداء / Lunch", "سعودي حجازي / Saudi Hijazi", "السعودية، الخليج والعامة", [("أرز مصري",10),("أرز بسمتي",7),("دجاج كامل مبرد",45),("حليب",18),("زبدة",3),("هيل",0.08)], "saudi"),
    spec("برياني سندي", "غداء / Lunch", "باكستاني / Pakistani", "باكستان", [("أرز بسمتي",18),("دجاج كامل مبرد",42),("زبادي",10),("طماطم",4),("بصل",5),("بهارات برياني",0.8)], "pakistan_heritage"),
    spec("كباب تشابلي", "غداء / Lunch", "باكستاني / Pakistani", "باكستان، أفغانستان", [("لحم مفروم",24),("بصل",5),("طماطم",3),("كزبرة خضراء",1),("ذرة مجروشة",2),("فلفل حار",0.4)], "pakistan"),
    spec("ساجي دجاج", "غداء / Lunch", "باكستاني / Pakistani", "باكستان", [("دجاج كامل مبرد",50),("ملح",0.7),("فلفل أسود",0.25),("ليمون",3),("أرز بسمتي",17)], "pakistan"),
    spec("أرز وكاري بنغلاديشي", "غداء / Lunch", "بنغلاديشي / Bangladeshi", "بنغلاديش", [("أرز بسمتي",17),("صدور دجاج",22),("عدس أحمر",6),("جزر",4),("طماطم",4),("كاري بودرة",0.6)], "bangladesh"),
    spec("ناسي توماتو", "غداء / Lunch", "ماليزي / Malaysian", "ماليزيا", [("أرز ياسمين",18),("صلصة طماطم جاهزة",5),("طماطم",4),("بصل",4),("قرفة عيدان",0.05),("صدور دجاج",20)], "malaysia"),
    spec("سامسا أوزبكية", "وجبة خفيفة / Snack", "أوزبكي / Uzbek", "أوزبكستان، كازاخستان، قرغيزستان، طاجيكستان", [("دقيق أبيض",14),("لحم مفروم",18),("بصل",6),("زيت نباتي",2),("كمون",0.25)], "uzbekistan"),
    spec("بالاليط خليجي", "إفطار / Breakfast", "خليجي / Gulf", "الإمارات العربية المتحدة، قطر، البحرين، الكويت، سلطنة عُمان", [("شعيرية",12),("بيض",100),("سكر",4),("هيل مطحون",0.08),("زعفران",2),("زيت نباتي",1.5)], "qatar"),
    spec("مدروبة سمك", "غداء / Lunch", "إماراتي / Emirati", "الإمارات العربية المتحدة، سلطنة عُمان", [("سمك فيليه",22),("أرز بسمتي",12),("طماطم",4),("بصل",4),("كركم",0.2),("كمون",0.2)], "uae"),
    spec("صالونة دجاج خليجية", "غداء / Lunch", "خليجي / Gulf", "الإمارات العربية المتحدة، قطر، البحرين، الكويت، سلطنة عُمان", [("دجاج كامل مبرد",42),("بطاطس",8),("جزر",5),("كوسة",5),("طماطم",5),("بصل",4)], "qatar"),
    spec("سارما ورق محشي", "غداء / Lunch", "تركي / Turkish", "تركيا، البوسنة والهرسك، ألبانيا", [("أرز بسمتي",12),("لحم مفروم",10),("بصل",4),("طماطم",3),("دبس رمان",1),("زيت نباتي",2)], "turkey"),
    spec("سيميت تركي", "إفطار / Breakfast", "تركي / Turkish", "تركيا", [("دقيق أبيض",14),("سمسم",2.5),("سكر",1),("زيت نباتي",1.5),("جبنة فيتا",8),("شاي",300)], "turkey"),
    spec("كباب تركي مشوي", "غداء / Lunch", "تركي / Turkish", "تركيا، البوسنة والهرسك، ألبانيا", [("لحم مفروم",24),("بصل",4),("بقدونس",1),("بابريكا",0.3),("خبز عربي",100),("طماطم",5)], "turkey"),
    spec("أرز وكاري سريلانكي", "غداء / Lunch", "سريلانكي / Sri Lankan", "سريلانكا", [("أرز بسمتي",17),("صدور دجاج",20),("حليب جوز الهند",8),("كاري بودرة",0.7),("عدس أحمر",5),("جزر",4)], "srilanka"),
    spec("هوبرز سريلانكية", "إفطار / Breakfast", "سريلانكي / Sri Lankan", "سريلانكا", [("أرز بسمتي",10),("حليب جوز الهند",8),("بيض",100),("سكر",1),("ملح",0.3)], "srilanka"),
    spec("كوتو روتي دجاج", "عشاء / Dinner", "سريلانكي / Sri Lankan", "سريلانكا", [("خبز براتا",100),("صدور دجاج",18),("بيض",50),("ملفوف",5),("جزر",4),("كاري بودرة",0.5)], "srilanka"),
    spec("بيتو وجوز الهند", "إفطار / Breakfast", "سريلانكي / Sri Lankan", "سريلانكا", [("أرز بسمتي",12),("جوز هند مبشور",5),("حليب جوز الهند",5),("سكر",2),("موز",10)], "srilanka"),
    spec("رشوف أردني", "غداء / Lunch", "أردني / Jordanian", "الأردن", [("عدس أخضر",8),("برغل",6),("زبادي",12),("بصل",5),("خبز عربي",100)], "jordan"),
    spec("دورو وات مع إنجيرا", "غداء / Lunch", "إثيوبي / Ethiopian", "إثيوبيا، إريتريا", [("دجاج كامل مبرد",42),("بصل",8),("طماطم",4),("بيض",50),("بابريكا",0.4),("دقيق أبيض",14)], "ethiopia"),
    spec("جياوزي دجاج وخضار", "عشاء / Dinner", "صيني / Chinese", "الصين", [("دقيق أبيض",14),("صدور دجاج",18),("ملفوف",6),("جزر",3),("صلصة صويا",2),("زنجبيل",0.5)], "china"),
    spec("نودلز صينية بالخضار", "غداء / Lunch", "صيني / Chinese", "الصين، سنغافورة", [("نودلز",16),("بروكلي",5),("جزر",4),("فلفل رومي",4),("صلصة صويا",3),("زيت نباتي",2)], "china"),
    spec("سويا دجاج نيجيري", "غداء / Lunch", "نيجيري / Nigerian", "نيجيريا، غانا، الكاميرون", [("صدور دجاج",25),("فول سوداني",3),("فلفل حار",0.4),("بابريكا",0.3),("بصل",4),("أرز بسمتي",16)], "nigeria"),
    spec("تشولي بهاتوري", "غداء / Lunch", "هندي / Indian", "الهند", [("حمص حب",14),("طماطم",4),("بصل",4),("جارام ماسالا",0.5),("دقيق أبيض",14),("زبادي",6)], "india"),
]

ALL_RC148_RECIPES = REPAIR_RECIPES + VERIFIED_RECIPES

# Complete operational menu reference for every Hajj mission country in master_data.MISSIONS.
# It is a recommendation/selection aid, not a claim that each dish is exclusive to that nationality.
GROUPS = {
    "south_asia": ["برياني دجاج هندي", "دجاج بالكاري", "تشانا مسالا", "روتي وخضار", "باراثا وبيض"],
    "se_asia": ["ناسي غورينغ", "ساتاي دجاج", "ناسي ليماك", "أرز إندونيسي بالدجاج", "نودلز دجاج بالخضار"],
    "central_asia": ["أرز أوزبكي بلوف", "مانتي", "لاجمان لحم", "سامسا أوزبكية", "دجاج مشوي وأرز"],
    "arab": ["كبسة دجاج", "مندي دجاج", "حمص وفلافل", "مقلوبة دجاج", "شاورما دجاج"],
    "gulf": ["كبسة دجاج سعودية", "مجبوس دجاج خليجي", "هريس دجاج خليجي", "صالونة دجاج خليجية", "بالاليط خليجي"],
    "maghreb": ["كسكس بالخضار واللحم", "طاجن دجاج", "شوربة حريرة", "مقرونة تونسية بالدجاج", "مكرونة مبكبكة"],
    "west_africa": ["جولوف رايس", "دجاج جولوف", "أرز وصلصة الفول السوداني", "شوربة إيجوسي باللحم", "دجاج مشوي وأرز"],
    "east_africa": ["إنجيرا يخنة دجاج", "دورو وات مع إنجيرا", "أرز صومالي بالدجاج", "دجاج مشوي وأرز", "خضار مشكلة وأرز"],
    "europe": ["دجاج مشوي بالبطاطس والأعشاب", "مكرونة بالدجاج", "سمك مشوي وأرز", "شوربة خضار", "ساندويتش دجاج"],
    "turk_balkan": ["أرز أوزي تركي", "شوربة عدس تركية", "كباب تركي مشوي", "سارما ورق محشي", "مانتي"],
    "china": ["دجاج حلو وحامض", "جياوزي دجاج وخضار", "نودلز صينية بالخضار", "أرز مقلي بالروبيان", "خضار مشكلة وأرز"],
    "srilanka": ["أرز وكاري سريلانكي", "كوتو روتي دجاج", "هوبرز سريلانكية", "بيتو وجوز الهند", "كاري سمك بنغلاديشي"],
}

NATIONALITY_GROUP = {
    "الهند":"south_asia","باكستان":"south_asia","بنغلاديش":"south_asia","أفغانستان":"south_asia","نيبال":"south_asia","المالديف":"south_asia",
    "إندونيسيا":"se_asia","ماليزيا":"se_asia","سنغافورة":"se_asia","تايلاند":"se_asia","الفلبين":"se_asia",
    "أوزبكستان":"central_asia","كازاخستان":"central_asia","قرغيزستان":"central_asia","طاجيكستان":"central_asia","تركمانستان":"central_asia",
    "تركيا":"turk_balkan","البوسنة والهرسك":"turk_balkan","ألبانيا":"turk_balkan",
    "الصين":"china","سريلانكا":"srilanka",
    "المغرب":"maghreb","الجزائر":"maghreb","تونس":"maghreb","ليبيا":"maghreb","موريتانيا":"maghreb",
    "نيجيريا":"west_africa","السنغال":"west_africa","مالي":"west_africa","تشاد":"west_africa","النيجر":"west_africa","غينيا":"west_africa","ساحل العاج":"west_africa","غانا":"west_africa","الكاميرون":"west_africa",
    "إثيوبيا":"east_africa","كينيا":"east_africa","تنزانيا":"east_africa","الصومال":"east_africa","جيبوتي":"east_africa",
    "المملكة المتحدة":"europe","فرنسا":"europe","ألمانيا":"europe","روسيا":"europe",
    "الكويت":"gulf","البحرين":"gulf","قطر":"gulf","الإمارات العربية المتحدة":"gulf","سلطنة عُمان":"gulf",
    "مصر":"arab","السودان":"arab","الأردن":"arab","فلسطين":"arab","العراق":"arab","سوريا":"arab","لبنان":"arab","اليمن":"arab",
}

NATIONALITY_MENU_REFERENCE = {country: GROUPS[group] for country, group in NATIONALITY_GROUP.items()}

# Trusted-name provenance for important recipes that already existed with valid ingredients.
def source_meta(source_key, note=""):
    authority, raw_url = SOURCES[source_key]
    url = _safe_data_url(raw_url)
    return {
        "source_authority": authority,
        "source_url": url,
        "verification_status": "رسمي موثق / Official Verified" if source_key != "nigeria" else "يحتاج مراجعة / Needs Review",
        "last_verified_on": "2026-08-09",
        "source_notes": (note + " " if note else "") + "المصدر يثبت اسم/هوية الطبق؛ صيغة وكميات WAFD التشغيلية مستقلة وتحتاج اعتماداً تشغيلياً.",
    }

SOURCE_METADATA = {
    "ريندانغ لحم": source_meta("indonesia"),
    "ناسي غورينغ": source_meta("indonesia"),
    "ساتيه دجاج بصلصة الفول": source_meta("malaysia"),
    "شوربة حريرة": source_meta("morocco"),
    "كسكس بالخضار والدجاج": source_meta("morocco"),
    "طاجن لحم بالبرقوق": source_meta("morocco"),
    "مجبوس دجاج خليجي": source_meta("qatar"),
    "هريس دجاج خليجي": source_meta("uae"),
    "منسف لحم أردني": source_meta("jordan"),
    "مقلوبة دجاج": source_meta("jordan"),
    "أرز جولوف بالدجاج": source_meta("nigeria"),
    "شوربة إيجوسي باللحم": source_meta("nigeria"),
    "بلوف أوزبكي": source_meta("uzbekistan"),
    "لاجمان لحم": source_meta("uzbekistan"),
    "كبسة دجاج": source_meta("saudi"),
    "جريش": source_meta("saudi"),
}
