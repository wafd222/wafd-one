"""Add editable multilingual display names to the operational cleaning catalog."""

import frappe


# ar: (en, bn, ur, hi, id, fr, ha, sw, uz)
TRANSLATIONS = {
    "منظف أرضيات مركز": ("Concentrated Floor Cleaner", "ঘন মেঝে পরিষ্কারক", "گاڑھا فرش صاف کرنے والا", "सांद्र फ़र्श क्लीनर", "Pembersih Lantai Konsentrat", "Nettoyant concentré pour sols", "Sinadarin wanke bene mai ƙarfi", "Kisafisha sakafu kilichokolezwa", "Konsentrlangan pol tozalagich"),
    "مطهر أسطح غذائي": ("Food-Safe Surface Disinfectant", "খাদ্য-নিরাপদ পৃষ্ঠ জীবাণুনাশক", "فوڈ سیف سطح جراثیم کش", "खाद्य-सुरक्षित सतह कीटाणुनाशक", "Disinfektan Permukaan Aman Pangan", "Désinfectant de surface alimentaire", "Maganin kashe ƙwayoyin saman abinci", "Kiuatilifu cha sehemu salama kwa chakula", "Oziq-ovqat uchun xavfsiz sirt dezinfektanti"),
    "سائل غسيل الصحون": ("Dishwashing Liquid", "বাসন ধোয়ার তরল", "برتن دھونے کا مائع", "बर्तन धोने का तरल", "Sabun Cuci Piring Cair", "Liquide vaisselle", "Ruwan wanke kwanoni", "Kioevu cha kuoshea vyombo", "Idish yuvish suyuqligi"),
    "مزيل دهون المطابخ": ("Kitchen Degreaser", "রান্নাঘরের তেল-ময়লা পরিষ্কারক", "باورچی خانے کا چکنائی صاف کرنے والا", "रसोई चिकनाई हटाने वाला", "Pembersih Lemak Dapur", "Dégraissant cuisine", "Mai cire maiko na kicin", "Kiondoa mafuta jikoni", "Oshxona yog‘ tozalagichi"),
    "كلور غذائي مخفف": ("Diluted Food-Safe Chlorine", "পাতলা খাদ্য-নিরাপদ ক্লোরিন", "ہلکا فوڈ سیف کلورین", "पतला खाद्य-सुरक्षित क्लोरीन", "Klorin Encer Aman Pangan", "Chlore alimentaire dilué", "Sinadarin chlorine na abinci mai laushi", "Klorini iliyopunguzwa salama kwa chakula", "Suyultirilgan oziq-ovqat xlor eritmasi"),
    "صابون يدين سائل": ("Liquid Hand Soap", "তরল হাতের সাবান", "مائع ہاتھ دھونے کا صابن", "तरल हाथ साबुन", "Sabun Tangan Cair", "Savon liquide pour les mains", "Sabunin hannu na ruwa", "Sabuni ya maji ya mikono", "Suyuq qo‘l sovuni"),
    "معقم يدين": ("Hand Sanitizer", "হ্যান্ড স্যানিটাইজার", "ہینڈ سینیٹائزر", "हैंड सैनिटाइज़र", "Pembersih Tangan", "Gel hydroalcoolique", "Maganin tsabtace hannu", "Kitakasa mikono", "Qo‘l antiseptigi"),
    "قفازات نيتريل": ("Nitrile Gloves", "নাইট্রাইল গ্লাভস", "نائٹرائل دستانے", "नाइट्राइल दस्ताने", "Sarung Tangan Nitril", "Gants en nitrile", "Safar hannu na nitrile", "Glavu za nitrile", "Nitril qo‘lqoplar"),
    "أكياس نفايات كبيرة": ("Large Waste Bags", "বড় আবর্জনার ব্যাগ", "بڑے کچرے کے تھیلے", "बड़े कचरा बैग", "Kantong Sampah Besar", "Grands sacs-poubelle", "Manyan buhunan shara", "Mifuko mikubwa ya taka", "Katta chiqindi paketlari"),
    "أكياس نفايات": ("Waste Bags", "আবর্জনার ব্যাগ", "کچرے کے تھیلے", "कचरा बैग", "Kantong Sampah", "Sacs-poubelle", "Buhunan shara", "Mifuko ya taka", "Chiqindi paketlari"),
    "مناديل تنظيف رول": ("Cleaning Wipes Roll", "ক্লিনিং ওয়াইপস রোল", "صفائی وائپس رول", "सफाई वाइप्स रोल", "Gulungan Lap Pembersih", "Rouleau de lingettes de nettoyage", "Nadin goge-goge na tsaftacewa", "Rolo ya vitambaa vya kusafisha", "Tozalash salfetkalari ruloni"),
    "إسفنجة تنظيف": ("Cleaning Sponge", "পরিষ্কারের স্পঞ্জ", "صفائی اسپنج", "सफाई स्पंज", "Spons Pembersih", "Éponge de nettoyage", "Soso na tsaftacewa", "Sifongo cha kusafisha", "Tozalash gubkasi"),
    "سلك تنظيف ستانلس": ("Stainless Steel Scourer", "স্টেইনলেস স্টিল স্ক্রাবার", "سٹین لیس اسٹیل اسکربر", "स्टेनलेस स्टील स्क्रबर", "Penggosok Baja Tahan Karat", "Tampon à récurer inox", "Abin goge bakin ƙarfe", "Kisugulio cha chuma cha pua", "Zanglamas po‘lat qirg‘ich"),
    "ممسحة أرضيات": ("Floor Mop", "মেঝে মোছার মপ", "فرش صاف کرنے کا موپ", "फ़र्श पोछा", "Pel Lantai", "Serpillière", "Abin goge bene", "Mopa ya sakafu", "Pol shvabrasi"),
    "فرشاة تنظيف": ("Cleaning Brush", "পরিষ্কারের ব্রাশ", "صفائی برش", "सफाई ब्रश", "Sikat Pembersih", "Brosse de nettoyage", "Burushin tsaftacewa", "Brashi ya kusafisha", "Tozalash cho‘tkasi"),
    "غطاء رأس استخدام واحد": ("Disposable Hair Cover", "একবার ব্যবহারযোগ্য হেয়ার কভার", "ایک بار استعمال کا ہیئر کور", "डिस्पोज़ेबल हेयर कवर", "Penutup Rambut Sekali Pakai", "Charlotte jetable", "Marufin kai na yarwa", "Kifuniko cha nywele cha matumizi moja", "Bir martalik soch qalpog‘i"),
    "كمامة استخدام واحد": ("Disposable Face Mask", "একবার ব্যবহারযোগ্য মাস্ক", "ایک بار استعمال کا ماسک", "डिस्पोज़ेबल मास्क", "Masker Sekali Pakai", "Masque jetable", "Takunkumin fuska na yarwa", "Barakoa ya matumizi moja", "Bir martalik niqob"),
    "مريلة استخدام واحد": ("Disposable Apron", "একবার ব্যবহারযোগ্য অ্যাপ্রন", "ایک بار استعمال کا ایپرن", "डिस्पोज़ेबल एप्रन", "Celemek Sekali Pakai", "Tablier jetable", "Atamfa ta yarwa", "Aproni ya matumizi moja", "Bir martalik fartuk"),
    "مقياس تركيز المطهر": ("Sanitizer Concentration Test Strips", "স্যানিটাইজার ঘনত্ব পরীক্ষার স্ট্রিপ", "سینیٹائزر مقدار جانچ پٹیاں", "सैनिटाइज़र सांद्रता टेस्ट स्ट्रिप्स", "Strip Uji Konsentrasi Sanitizer", "Bandelettes de contrôle du désinfectant", "Takardun gwajin ƙarfin sanitizer", "Vipande vya kupima mkusanyiko wa sanitizer", "Antiseptik konsentratsiyasi test tasmalari"),
    "شرائط فحص تعقيم": ("Sanitizer Test Strips", "স্যানিটাইজার পরীক্ষার স্ট্রিপ", "سینیٹائزر ٹیسٹ پٹیاں", "सैनिटाइज़र टेस्ट स्ट्रिप्स", "Strip Uji Sanitizer", "Bandelettes de test désinfectant", "Takardun gwajin sanitizer", "Vipande vya kupima sanitizer", "Antiseptik test tasmalari"),
}

FIELDS = (
    "ingredient_name_en", "ingredient_name_bn", "ingredient_name_ur",
    "ingredient_name_hi", "ingredient_name_id", "ingredient_name_fr",
    "ingredient_name_ha", "ingredient_name_sw", "ingredient_name_uz",
)


def execute():
    frappe.reload_doc("wafd_one", "doctype", "wafd_ingredient", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_cleaning_home", force=True)
    frappe.reload_doc("wafd_one", "page", "wafd_storekeeper_home", force=True)
    for ingredient, translated in TRANSLATIONS.items():
        name = frappe.db.get_value("WAFD Ingredient", {"ingredient_name": ingredient}, "name")
        if not name:
            continue
        current = frappe.db.get_value("WAFD Ingredient", name, list(FIELDS), as_dict=True)
        values = {
            field: value for field, value in zip(FIELDS, translated)
            if not current.get(field)
        }
        if values:
            frappe.db.set_value("WAFD Ingredient", name, values, update_modified=False)
    frappe.clear_cache(doctype="WAFD Ingredient")
    frappe.clear_cache(doctype="Page")
