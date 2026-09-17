frappe.pages["wafd-role-home"].on_page_load = function (wrapper) {
  document.body.classList.add("wafd-at-role-home");
  // RC217: the home page must never carry the global mobile back control.
  document.getElementById("wafd-global-mobile-back")?.remove();
  document.getElementById("wafd-mobile-back-v218")?.remove();
  document.getElementById("wafd-mobile-back-v219")?.remove();
  $(wrapper).addClass("wafd-role-home-page");
  const roles = new Set(frappe.user_roles || []);
  const isExecutive = roles.has("System Manager") || roles.has("WAFD Operations Manager");
  const mobileUa = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || "");
  const touchDevice = (navigator.maxTouchPoints || 0) > 0 && window.screen.width <= 1200;
  const isMobile = window.matchMedia("(max-width: 900px)").matches || mobileUa || touchDevice;

  // Managers retain the approved executive command center on desktop.
  // On phones/tablets they get the compact role home first, with an explicit
  // link to the full dashboard when they need the complete management view.
  if (isExecutive && !isMobile) {
    frappe.set_route("wafd-one-dashboard");
    return;
  }

  const page = frappe.ui.make_app_page({ parent: wrapper, title: __("WAFD ONE"), single_column: true });
  const $root = $(page.body).attr("dir", "rtl");
  const currentUser = frappe.user.full_name() || frappe.session.user;
  const today = frappe.datetime.str_to_user(frappe.datetime.get_today());
  const LANGS = { ar:"العربية", en:"English", id:"Bahasa Indonesia", ur:"اردو", hi:"हिन्दी", bn:"বাংলা", fr:"Français (Afrique/Mali)", ha:"Hausa", sw:"Kiswahili", uz:"Oʻzbekcha" };
  let uiLang = localStorage.getItem("wafd_lang") || "ar";
  if (!LANGS[uiLang]) uiLang = "ar";
  const D = {
    "الإدارة":{en:"Management",id:"Manajemen",ur:"انتظامیہ",hi:"प्रबंधन",bn:"ব্যবস্থাপনা",fr:"Direction",ha:"Gudanarwa",sw:"Usimamizi",uz:"Boshqaruv"},
    "مدير العمليات":{en:"Operations Manager",id:"Manajer Operasional",ur:"آپریشنز مینیجر",hi:"ऑपरेशंस मैनेजर",bn:"অপারেশন ম্যানেজার",fr:"Responsable des opérations",ha:"Manajan Ayyuka",sw:"Meneja wa Uendeshaji",uz:"Operatsiyalar menejeri"},
    "مدير المشروع":{en:"Project Manager",id:"Manajer Proyek",ur:"پروجیکٹ مینیجر",hi:"परियोजना प्रबंधक",bn:"প্রকল্প ব্যবস্থাপক",fr:"Chef de projet",ha:"Manajan Aiki",sw:"Meneja wa Mradi",uz:"Loyiha menejeri"},
    "مشرف الإنتاج":{en:"Production Supervisor",id:"Supervisor Produksi",ur:"پروڈکشن سپروائزر",hi:"उत्पादन पर्यवेक्षक",bn:"উৎপাদন সুপারভাইজার",fr:"Superviseur de production",ha:"Mai Kula da Samarwa",sw:"Msimamizi wa Uzalishaji",uz:"Ishlab chiqarish nazoratchisi"},
    "مفتش الجودة":{en:"Quality Inspector",id:"Inspektur Kualitas",ur:"کوالٹی انسپکٹر",hi:"गुणवत्ता निरीक्षक",bn:"মান পরিদর্শক",fr:"Inspecteur qualité",ha:"Mai Duba Inganci",sw:"Mkaguzi wa Ubora",uz:"Sifat inspektori"},
    "أمين المستودع":{en:"Storekeeper",id:"Petugas Gudang",ur:"اسٹور کیپر",hi:"भंडार प्रभारी",bn:"স্টোরকিপার",fr:"Magasinier",ha:"Mai Kula da Rumbu",sw:"Mhifadhi wa Ghala",uz:"Omborchi"},
    "مشرف النظافة":{en:"Cleaning Supervisor",id:"Supervisor Kebersihan",ur:"صفائی سپروائزر",hi:"सफाई पर्यवेक्षक",bn:"পরিচ্ছন্নতা সুপারভাইজার",fr:"Superviseur nettoyage",ha:"Mai Kula da Tsafta",sw:"Msimamizi wa Usafi",uz:"Tozalash nazoratchisi"},
    "مشرف التوصيل":{en:"Delivery Supervisor",id:"Supervisor Pengiriman",ur:"ڈیلیوری سپروائزر",hi:"डिलीवरी पर्यवेक्षक",bn:"ডেলিভারি সুপারভাইজার",fr:"Superviseur livraison",ha:"Mai Kula da Isarwa",sw:"Msimamizi wa Usafirishaji",uz:"Yetkazib berish nazoratchisi"},
    "السائق":{en:"Driver",id:"Pengemudi",ur:"ڈرائیور",hi:"चालक",bn:"চালক",fr:"Chauffeur",ha:"Direba",sw:"Dereva",uz:"Haydovchi"},
    "متابعة التسليم":{en:"Delivery Tracking",id:"Pelacakan Pengiriman",ur:"ڈیلیوری ٹریکنگ",hi:"डिलीवरी ट्रैकिंग",bn:"ডেলিভারি ট্র্যাকিং",fr:"Suivi des livraisons",ha:"Bibiyar Isarwa",sw:"Ufuatiliaji wa Usafirishaji",uz:"Yetkazib berishni kuzatish"},
    "بيانات التسليم":{en:"Delivery Data",id:"Data Pengiriman",ur:"ڈیلیوری ڈیٹا",hi:"डिलीवरी डेटा",bn:"ডেলিভারি তথ্য",fr:"Données de livraison",ha:"Bayanan Isarwa",sw:"Taarifa za Usafirishaji",uz:"Yetkazib berish ma'lumotlari"},
    "بيانات الرحلات المسندة لحسابك":{en:"Deliveries assigned to your account",id:"Pengiriman yang ditugaskan ke akun Anda",ur:"آپ کے اکاؤنٹ کو تفویض کردہ ڈیلیوری",hi:"आपके खाते को सौंपी गई डिलीवरी",bn:"আপনার অ্যাকাউন্টে নির্ধারিত ডেলিভারি",fr:"Livraisons attribuées à votre compte",ha:"Isarwar da aka ba asusunka",sw:"Usafirishaji uliopangiwa akaunti yako",uz:"Hisobingizga biriktirilgan yetkazmalar"},
    "عرض الرحلات المسندة وصور التسليم للقراءة فقط":{en:"View assigned trips and delivery proof as read-only",id:"Lihat perjalanan dan bukti pengiriman hanya-baca",ur:"تفویض کردہ سفر اور ثبوت صرف پڑھنے کے لیے",hi:"सौंपी गई यात्राएँ और प्रमाण केवल पढ़ें",bn:"নির্ধারিত ট্রিপ ও প্রমাণ শুধু দেখুন",fr:"Consulter les trajets et preuves en lecture seule",ha:"Duba tafiye-tafiye da hujjar isarwa kawai",sw:"Tazama safari na uthibitisho bila kuhariri",uz:"Biriktirilgan safarlar va dalillarni faqat ko‘rish"},
    "المالية":{en:"Finance",id:"Keuangan",ur:"مالیات",hi:"वित्त",bn:"অর্থ",fr:"Finance",ha:"Kuɗi",sw:"Fedha",uz:"Moliya"},
    "المعتمد":{en:"Approver",id:"Penyetuju",ur:"منظور کنندہ",hi:"अनुमोदक",bn:"অনুমোদনকারী",fr:"Approbateur",ha:"Mai Amincewa",sw:"Muidhinishaji",uz:"Tasdiqlovchi"},
    "المدقق":{en:"Auditor",id:"Auditor",ur:"آڈیٹر",hi:"ऑडिटर",bn:"নিরীক্ষক",fr:"Auditeur",ha:"Mai Bincike",sw:"Mkaguzi",uz:"Auditor"},
    "مسؤول عروض الأسعار":{en:"Quotation Officer"},
    "إنشاء وإرسال ومتابعة عروض الأسعار":{en:"Create, send, and track quotations"},
    "جميع عروض الأسعار":{en:"All Quotations"},
    "مراجعة جميع العروض وحالاتها":{en:"Review all quotations and their status"},
    "مهام متعددة":{en:"Multiple Tasks",id:"Beberapa Tugas",ur:"متعدد ذمہ داریاں",hi:"कई कार्य",bn:"একাধিক কাজ",fr:"Tâches multiples",ha:"Ayyuka da yawa",sw:"Majukumu mengi",uz:"Bir nechta vazifa"},
    "الأدوات المصرح بها حسب المهمات المسندة":{en:"Tools allowed by the assigned tasks",id:"Alat sesuai tugas yang diberikan",ur:"تفویض کردہ کاموں کے مطابق ٹولز",hi:"सौंपे गए कार्यों के अनुसार उपकरण",bn:"নির্ধারিত কাজ অনুযায়ী সরঞ্জাম",fr:"Outils autorisés selon les tâches attribuées",ha:"Kayan aiki bisa ayyukan da aka ba ka",sw:"Zana kulingana na majukumu uliyopewa",uz:"Berilgan vazifalarga mos vositalar"},
    "الرئيسية":{en:"Home",id:"Beranda",ur:"ہوم",hi:"होम",bn:"হোম",fr:"Accueil",ha:"Gida",sw:"Nyumbani",uz:"Bosh sahifa"},
    "تسجيل الخروج":{en:"Logout",id:"Keluar",ur:"لاگ آؤٹ",hi:"लॉग आउट",bn:"লগ আউট",fr:"Déconnexion",ha:"Fita",sw:"Ondoka",uz:"Chiqish"},
    "لوحة الإدارة الكاملة":{en:"Full Management Dashboard",id:"Dasbor Manajemen Lengkap",ur:"مکمل انتظامی ڈیش بورڈ",hi:"पूर्ण प्रबंधन डैशबोर्ड",bn:"সম্পূর্ণ ব্যবস্থাপনা ড্যাশবোর্ড",fr:"Tableau de bord complet",ha:"Cikakken Dashboard",sw:"Dashibodi Kamili",uz:"To‘liq boshqaruv paneli"},
    "التشغيل":{en:"Operations",id:"Operasional",ur:"آپریشنز",hi:"संचालन",bn:"অপারেশন",fr:"Opérations",ha:"Ayyuka",sw:"Uendeshaji",uz:"Operatsiyalar"},
    "المخزون والمشتريات":{en:"Inventory & Purchasing",id:"Stok & Pembelian",ur:"اسٹاک اور خریداری",hi:"स्टॉक और खरीद",bn:"স্টক ও ক্রয়",fr:"Stock & Achats",ha:"Kaya & Saye",sw:"Stoo & Ununuzi",uz:"Ombor & Xarid"},
    "التوصيل":{en:"Delivery",id:"Pengiriman",ur:"ترسیل",hi:"डिलीवरी",bn:"ডেলিভারি",fr:"Livraison",ha:"Isarwa",sw:"Usafirishaji",uz:"Yetkazib berish"},
    "إفطار صائم":{en:"Iftar Saim",id:"Iftar Saim",ur:"افطار صائم",hi:"इफ्तार साइम",bn:"ইফতার সায়েম",fr:"Iftar Saim",ha:"Iftar Saim",sw:"Iftar Saim",uz:"Iftar Saim"},
    "المستندات والتعهدات":{en:"Documents & Undertakings",id:"Dokumen & Pernyataan",ur:"دستاویزات و تعہدات",hi:"दस्तावेज़ और प्रतिज्ञाएँ",bn:"নথি ও অঙ্গীকার",fr:"Documents & Engagements",ha:"Takardu",sw:"Nyaraka",uz:"Hujjatlar"},
    "إدارة الموظفين":{en:"Employee Management"},
    "إضافة الحسابات وتحديد المهمات":{en:"Create accounts and assign tasks"},
    "المشاريع":{en:"Projects",id:"Proyek",ur:"منصوبے",hi:"परियोजनाएँ",bn:"প্রকল্প",fr:"Projets",ha:"Ayyuka",sw:"Miradi",uz:"Loyihalar"},
    "الخطط اليومية":{en:"Daily Plans",id:"Rencana Harian",ur:"روزانہ منصوبے",hi:"दैनिक योजनाएँ",bn:"দৈনিক পরিকল্পনা",fr:"Plans quotidiens",ha:"Tsare-tsaren Yau",sw:"Mipango ya Kila Siku",uz:"Kunlik rejalar"},
    "المستندات":{en:"Documents",id:"Dokumen",ur:"دستاویزات",hi:"दस्तावेज़",bn:"নথি",fr:"Documents",ha:"Takardu",sw:"Nyaraka",uz:"Hujjatlar"},
    "عروض الأسعار":{en:"Quotations",id:"Penawaran",ur:"قیمت کی پیشکشیں",hi:"कोटेशन",bn:"মূল্য প্রস্তাব",fr:"Devis",ha:"Kalaman farashi",sw:"Nukuu",uz:"Tijorat takliflari"},
    "إنشاء عرض سعر":{en:"Create Quotation",id:"Buat Penawaran",ur:"کوٹیشن بنائیں",hi:"कोटेशन बनाएँ",bn:"মূল্য প্রস্তাব তৈরি",fr:"Créer un devis",ha:"Ƙirƙiri kalaman farashi",sw:"Unda Nukuu",uz:"Taklif yaratish"},
    "إعداد عرض جديد للعميل":{en:"Prepare a new customer quotation"},
    "العروض المرسلة":{en:"Sent Quotations",id:"Penawaran Terkirim",ur:"بھیجے گئے کوٹیشن",hi:"भेजे गए कोटेशन",bn:"প্রেরিত মূল্য প্রস্তাব",fr:"Devis envoyés",ha:"Kalaman farashi da aka aika",sw:"Nukuu Zilizotumwa",uz:"Yuborilgan takliflar"},
    "فقط العروض التي تمت مشاركتها وتسجيل إرسالها":{en:"Only quotations that were shared and recorded as sent"},
    "المسودات والمعتمدة والمرسلة وجميع الحالات":{en:"Draft, approved, sent, and every quotation status"},
    "مراجعة واعتماد عروض الأسعار":{en:"Review and approve quotations"},
    "دفعات الإنتاج":{en:"Production Batches",id:"Batch Produksi",ur:"پروڈکشن بیچز",hi:"उत्पादन बैच",bn:"উৎপাদন ব্যাচ",fr:"Lots de production",ha:"Rukunin Samarwa",sw:"Makundi ya Uzalishaji",uz:"Ishlab chiqarish partiyalari"},
    "سجلات التغليف":{en:"Packaging Records",id:"Catatan Pengemasan",ur:"پیکنگ ریکارڈز",hi:"पैकेजिंग रिकॉर्ड",bn:"প্যাকেজিং রেকর্ড",fr:"Registres d’emballage",ha:"Bayanan Marufi",sw:"Rekodi za Ufungashaji",uz:"Qadoqlash yozuvlari"},
    "الوصفات":{en:"Recipes",id:"Resep",ur:"ترکیبیں",hi:"रेसिपी",bn:"রেসিপি",fr:"Recettes",ha:"Girke-girke",sw:"Mapishi",uz:"Retseptlar"},
    "فحص الجودة":{en:"Quality Inspection",id:"Inspeksi Kualitas",ur:"کوالٹی معائنہ",hi:"गुणवत्ता निरीक्षण",bn:"মান পরীক্ষা",fr:"Contrôle qualité",ha:"Duba Inganci",sw:"Ukaguzi wa Ubora",uz:"Sifat tekshiruvi"},
    "فحوص CCP":{en:"CCP Checks",id:"Pemeriksaan CCP",ur:"CCP چیکس",hi:"CCP जांच",bn:"CCP পরীক্ষা",fr:"Contrôles CCP",ha:"Binciken CCP",sw:"Ukaguzi wa CCP",uz:"CCP tekshiruvlari"},
    "حركات المخزون":{en:"Stock Movements",id:"Pergerakan Stok",ur:"اسٹاک موومنٹس",hi:"स्टॉक मूवमेंट",bn:"স্টক মুভমেন্ট",fr:"Mouvements de stock",ha:"Motsin Kaya",sw:"Mienendo ya Stoo",uz:"Ombor harakatlari"},
    "أرصدة المخزون":{en:"Stock Balances",id:"Saldo Stok",ur:"اسٹاک بیلنس",hi:"स्टॉक बैलेंस",bn:"স্টক ব্যালেন্স",fr:"Soldes de stock",ha:"Ma'aunin Kaya",sw:"Salio la Stoo",uz:"Ombor qoldiqlari"},
    "أوامر الشراء":{en:"Purchase Orders",id:"Pesanan Pembelian",ur:"خریداری آرڈرز",hi:"खरीद आदेश",bn:"ক্রয় আদেশ",fr:"Bons de commande",ha:"Odar Saye",sw:"Oda za Ununuzi",uz:"Xarid buyurtmalari"},
    "إدارة المخزون":{en:"Manage Inventory"},
    "شاشة سهلة للاستلام والصرف والتحويل والأرصدة":{en:"Simple receiving, issuing, transfer, and balance screen"},
    "استلام مواد مشتراة":{en:"Receive Purchased Materials"},
    "تسجيل المواد الواردة من أمر الشراء":{en:"Record materials received against a purchase order"},
    "صرف مواد":{en:"Issue Materials"},
    "تسجيل المواد الخارجة من المستودع":{en:"Record materials leaving the warehouse"},
    "تحويل مواد":{en:"Transfer Materials"},
    "نقل المواد بين المستودعات":{en:"Move materials between warehouses"},
    "ثلاث مهام عملية للمخزون":{en:"Three practical inventory tasks",id:"Tiga tugas stok praktis",ur:"اسٹاک کے تین عملی کام",hi:"तीन व्यावहारिक स्टॉक कार्य",bn:"তিনটি ব্যবহারিক স্টক কাজ",fr:"Trois tâches pratiques de stock",ha:"Ayyukan kaya uku masu sauƙi",sw:"Kazi tatu rahisi za stoo",uz:"Uchta amaliy ombor vazifasi"},
    "استلام وتوزيع المشتريات":{en:"Receive and Distribute Purchases",id:"Terima dan Distribusikan Pembelian",ur:"خریداری وصول اور تقسیم کریں",hi:"खरीद प्राप्त और वितरित करें",bn:"ক্রয় গ্রহণ ও বিতরণ",fr:"Réceptionner et distribuer les achats",ha:"Karɓa da Rarraba Sayayya",sw:"Pokea na Sambaza Manunuzi",uz:"Xaridlarni qabul qilish va tarqatish"},
    "إدخال المواد في المستودعات والثلاجات بسهولة":{en:"Put materials into warehouses and cold rooms easily",id:"Masukkan bahan ke gudang dan ruang dingin dengan mudah",ur:"سامان آسانی سے گودام اور کولڈ روم میں درج کریں",hi:"सामग्री आसानी से गोदाम और कोल्ड रूम में दर्ज करें",bn:"সহজে গুদাম ও কোল্ড রুমে সামগ্রী যোগ করুন",fr:"Entrer facilement les articles dans les magasins et chambres froides",ha:"Saka kaya cikin rumbuna da ɗakunan sanyi cikin sauƙi",sw:"Ingiza vifaa kwa urahisi kwenye maghala na vyumba baridi",uz:"Materiallarni ombor va sovuq xonalarga oson kiriting"},
    "تسليم مواد للموظفين":{en:"Hand Over Materials to Employees",id:"Serahkan Bahan kepada Karyawan",ur:"ملازمین کو سامان دیں",hi:"कर्मचारियों को सामग्री सौंपें",bn:"কর্মীদের সামগ্রী হস্তান্তর",fr:"Remettre des articles aux employés",ha:"Miƙa Kaya ga Ma'aikata",sw:"Kabidhi Vifaa kwa Wafanyakazi",uz:"Materiallarni xodimlarga topshirish"},
    "اختيار الوظيفة والاسم والمستودع ثم المواد":{en:"Choose the job, employee name, warehouse, then materials",id:"Pilih jabatan, nama, gudang, lalu bahan",ur:"عہدہ، نام، گودام پھر سامان منتخب کریں",hi:"पद, नाम, गोदाम और फिर सामग्री चुनें",bn:"পদ, নাম, গুদাম, তারপর সামগ্রী নির্বাচন করুন",fr:"Choisir le poste, le nom, le magasin puis les articles",ha:"Zaɓi aiki, suna, rumbu sannan kaya",sw:"Chagua kazi, jina, ghala kisha vifaa",uz:"Lavozim, ism, ombor va materiallarni tanlang"},
    "معلومات المخزون":{en:"Inventory Information",id:"Informasi Stok",ur:"اسٹاک کی معلومات",hi:"स्टॉक जानकारी",bn:"স্টক তথ্য",fr:"Informations de stock",ha:"Bayanan Kaya",sw:"Taarifa za Stoo",uz:"Ombor ma'lumotlari"},
    "الأرصدة والنواقص وتنبيهات انتهاء الصلاحية":{en:"Balances, shortages, and expiry alerts",id:"Saldo, kekurangan, dan peringatan kedaluwarsa",ur:"بیلنس، کمی اور میعاد ختم ہونے کی اطلاعات",hi:"शेष, कमी और समाप्ति अलर्ट",bn:"ব্যালেন্স, ঘাটতি ও মেয়াদ সতর্কতা",fr:"Soldes, manques et alertes d'expiration",ha:"Ma'auni, ƙaranci da faɗakarwar ƙarewa",sw:"Salio, upungufu na tahadhari za muda",uz:"Qoldiq, kamomad va yaroqlilik ogohlantirishlari"},
    "مواد النظافة المصروفة لك فقط":{en:"Only cleaning materials issued to you",id:"Hanya bahan kebersihan yang diberikan kepada Anda",ur:"صرف آپ کو جاری کردہ صفائی کا سامان",hi:"केवल आपको जारी सफाई सामग्री",bn:"শুধু আপনাকে দেওয়া পরিচ্ছন্নতার সামগ্রী",fr:"Uniquement les produits de nettoyage qui vous sont attribués",ha:"Kayan tsaftacewa da aka ba ka kawai",sw:"Vifaa vya usafi ulivyopewa pekee",uz:"Faqat sizga berilgan tozalash materiallari"},
    "استلام وصرف مواد النظافة":{en:"Receive and Use Cleaning Materials",id:"Terima dan Gunakan Bahan Kebersihan",ur:"صفائی کا سامان وصول اور استعمال کریں",hi:"सफाई सामग्री प्राप्त और उपयोग करें",bn:"পরিচ্ছন্নতার সামগ্রী গ্রহণ ও ব্যবহার",fr:"Recevoir et utiliser les produits de nettoyage",ha:"Karɓa da Amfani da Kayan Tsafta",sw:"Pokea na Tumia Vifaa vya Usafi",uz:"Tozalash materiallarini qabul qilish va ishlatish"},
    "تأكيد الاستلام وتسجيل المواد المستخدمة من شاشة واحدة":{en:"Confirm receipt and record used materials on one screen",id:"Konfirmasi penerimaan dan catat pemakaian dalam satu layar",ur:"ایک اسکرین پر وصولی اور استعمال درج کریں",hi:"एक स्क्रीन पर प्राप्ति और उपयोग दर्ज करें",bn:"এক স্ক্রিনে গ্রহণ নিশ্চিত ও ব্যবহার লিখুন",fr:"Confirmer la réception et enregistrer l'utilisation sur un seul écran",ha:"Tabbatar da karɓa da rubuta amfani a allo ɗaya",sw:"Thibitisha mapokezi na rekodi matumizi kwenye skrini moja",uz:"Qabul qilish va sarfni bitta ekranda qayd eting"},
    "المركبة والوجهة وحالة الرحلة":{en:"Vehicle, destination, and trip status",id:"Kendaraan, tujuan, dan status perjalanan",ur:"گاڑی، منزل اور سفر کی حالت",hi:"वाहन, गंतव्य और यात्रा स्थिति",bn:"যানবাহন, গন্তব্য ও ট্রিপের অবস্থা",fr:"Véhicule, destination et état du trajet",ha:"Mota, wurin zuwa da matsayin tafiya",sw:"Gari, mahali na hali ya safari",uz:"Transport, manzil va safar holati"},
    "مخزون أدوات النظافة":{en:"Cleaning Supplies Stock",id:"Stok Peralatan Kebersihan",ur:"صفائی سامان اسٹاک",hi:"सफाई सामग्री स्टॉक",bn:"পরিচ্ছন্নতা সামগ্রী স্টক",fr:"Stock de nettoyage",ha:"Kayan Tsafta",sw:"Stoo ya Vifaa vya Usafi",uz:"Tozalash vositalari ombori"},
    "المواد المصروفة لي":{en:"Materials Issued to Me",id:"Bahan Dikeluarkan untuk Saya",ur:"مجھے جاری کردہ مواد",hi:"मुझे जारी सामग्री",bn:"আমাকে ইস্যু করা সামগ্রী",fr:"Articles qui me sont attribués",ha:"Kayan da aka ba ni",sw:"Vifaa Nilivyopewa",uz:"Menga berilgan materiallar"},
    "رحلات التوصيل":{en:"Delivery Trips",id:"Perjalanan Pengiriman",ur:"ڈیلیوری ٹرپس",hi:"डिलीवरी यात्राएँ",bn:"ডেলিভারি ট্রিপ",fr:"Trajets de livraison",ha:"Tafiyar Isarwa",sw:"Safari za Usafirishaji",uz:"Yetkazib berish safarlari"},
    "خطة التوصيل والمواقع والسائقون":{en:"Delivery plans, destinations, and drivers"},
    "إدارة التوصيل":{en:"Delivery Management"},
    "إنشاء الرحلات والجداول ومتابعة التسليم":{en:"Create deliveries and schedules, and track completion"},
    "إضافة رحلة وتعيين سائق":{en:"Add Delivery and Assign Driver"},
    "اختر الفندق أو الموقع والوقت والسائق":{en:"Choose destination, time, and driver"},
    "الرحلات الحالية":{en:"Current Deliveries"},
    "متابعة استلام السائق والتوجه للموقع":{en:"Track driver acceptance and travel"},
    "سجل التسليم":{en:"Delivery Records"},
    "الوقت والموقع وصورة إثبات كل تسليم":{en:"Time, location, and photo for every delivery"},
    "المواقع والفنادق":{en:"Locations and Hotels"},
    "إضافة فندق أو مسجد أو موقع إفطار صائم":{en:"Add a hotel, mosque, or Iftar site"},
    "سجلات التحميل":{en:"Loading Records",id:"Catatan Pemuatan",ur:"لوڈنگ ریکارڈز",hi:"लोडिंग रिकॉर्ड",bn:"লোডিং রেকর্ড",fr:"Registres de chargement",ha:"Bayanan Lodi",sw:"Rekodi za Upakiaji",uz:"Yuklash yozuvlari"},
    "سندات التسليم":{en:"Delivery Notes",id:"Surat Pengiriman",ur:"ڈیلیوری نوٹس",hi:"डिलीवरी नोट",bn:"ডেলিভারি নোট",fr:"Bons de livraison",ha:"Takardar Isarwa",sw:"Hati za Uwasilishaji",uz:"Yetkazib berish hujjatlari"},
    "سندات الاستلام":{en:"Receiving Notes",id:"Bukti Penerimaan",ur:"وصولی نوٹس",hi:"प्राप्ति नोट",bn:"রিসিভিং নোট",fr:"Bons de réception",ha:"Takardar Karɓa",sw:"Hati za Kupokea",uz:"Qabul hujjatlari"},
    "رحلاتي":{en:"My Trips",id:"Perjalanan Saya",ur:"میری ٹرپس",hi:"मेरी यात्राएँ",bn:"আমার ট্রিপ",fr:"Mes trajets",ha:"Tafiyoyina",sw:"Safari Zangu",uz:"Safarlarim"},
    "الفواتير":{en:"Invoices",id:"Faktur",ur:"انوائسز",hi:"चालान",bn:"ইনভয়েস",fr:"Factures",ha:"Rasitu",sw:"Ankara",uz:"Hisob-fakturalar"},
    "التحصيل":{en:"Collections",id:"Pembayaran",ur:"وصولیاں",hi:"वसूली",bn:"আদায়",fr:"Encaissements",ha:"Tarin Kuɗi",sw:"Makusanyo",uz:"To‘lovlar"},
    "العقود":{en:"Contracts",id:"Kontrak",ur:"معاہدے",hi:"अनुबंध",bn:"চুক্তি",fr:"Contrats",ha:"Kwangiloli",sw:"Mikataba",uz:"Shartnomalar"},
    "طلبات الاعتماد":{en:"Approval Requests",id:"Permintaan Persetujuan",ur:"منظوری درخواستیں",hi:"अनुमोदन अनुरोध",bn:"অনুমোদন অনুরোধ",fr:"Demandes d’approbation",ha:"Buƙatun Amincewa",sw:"Maombi ya Uidhinishaji",uz:"Tasdiqlash so‘rovlari"},
    "المستخدم":{en:"User",id:"Pengguna",ur:"صارف",hi:"उपयोगकर्ता",bn:"ব্যবহারকারী",fr:"Utilisateur",ha:"Mai amfani",sw:"Mtumiaji",uz:"Foydalanuvchi"},
    "الدور":{en:"Role",id:"Peran",ur:"کردار",hi:"भूमिका",bn:"ভূমিকা",fr:"Rôle",ha:"Matsayi",sw:"Jukumu",uz:"Rol"},
    "التاريخ":{en:"Date",id:"Tanggal",ur:"تاریخ",hi:"तारीख",bn:"তারিখ",fr:"Date",ha:"Kwanan wata",sw:"Tarehe",uz:"Sana"},
    "تظهر لك فقط الوظائف والبيانات التي يسمح بها دورك في النظام.":{en:"Only functions and data allowed by your system role are shown.",id:"Hanya fungsi dan data yang diizinkan oleh peran Anda yang ditampilkan.",ur:"صرف وہی افعال اور ڈیٹا دکھایا جاتا ہے جو آپ کے کردار کو اجازت ہے۔",hi:"केवल आपकी भूमिका द्वारा अनुमत कार्य और डेटा दिखाए जाते हैं।",bn:"শুধু আপনার ভূমিকা অনুযায়ী অনুমোদিত কাজ ও তথ্য দেখানো হয়।",fr:"Seules les fonctions et données autorisées par votre rôle sont affichées.",ha:"Ana nuna ayyuka da bayanan da matsayinka ya ba da izini kawai.",sw:"Kazi na data zinazoruhusiwa na jukumu lako pekee ndizo huonekana.",uz:"Faqat rolingiz ruxsat bergan funksiyalar va ma’lumotlar ko‘rsatiladi."}
  };
  const tr = (text) => text === "اللغة" ? ({ar:"اللغة",en:"Language",id:"Bahasa",ur:"زبان",hi:"भाषा",bn:"ভাষা",fr:"Langue",ha:"Harshe",sw:"Lugha",uz:"Til"}[uiLang]||"Language") : uiLang === "ar" ? text : (D[text] && (D[text][uiLang] || D[text].en)) || text;
  const rtl = () => ["ar","ur"].includes(uiLang);

  const profiles = [
    {
      role: "WAFD Undertaking Officer", title: "مسؤول التعهدات", subtitle: "إنشاء واعتماد وإرسال التعهدات",
      items: [
        { label: "إنشاء تعهد", desc: "تسجيل بيانات تعهد جديد بالكامل", icon: "✦", new_doctype: "WAFD Hotel Undertaking", primary: true },
        { label: "إضافة فندق", desc: "إضافة فندق غير موجود بالقائمة", icon: "＋", action: "new_hotel" },
        { label: "تعهداتي", desc: "مراجعة واعتماد ومشاركة التعهدات التي أعددتها", icon: "▤", doctype: "WAFD Hotel Undertaking" }
      ]
    },
    {
      role: "WAFD Undertaking Reviewer", title: "مراجع التعهدات", subtitle: "مراجعة جميع التعهدات ومعرفة من أعدّها",
      items: [
        { label: "مراجعة التعهدات", desc: "جميع التعهدات واسم مُعدّ كل تعهد", icon: "▤", doctype: "WAFD Hotel Undertaking", primary: true }
      ]
    },
    {
      role: "WAFD Quotation Officer", title: "مسؤول عروض الأسعار", subtitle: "إنشاء وإرسال ومتابعة عروض الأسعار",
      items: [
        { label: "إنشاء عرض سعر", desc: "إعداد عرض جديد للعميل", icon: "💼", new_doctype: "WAFD Quotation", primary: true },
        { label: "العروض المرسلة", desc: "فقط العروض التي تمت مشاركتها وتسجيل إرسالها", icon: "✓", doctype: "WAFD Quotation", filters: { sent_on: ["is", "set"] } },
        { label: "جميع عروض الأسعار", desc: "المسودات والمعتمدة والمرسلة وجميع الحالات", icon: "▤", doctype: "WAFD Quotation" }
      ]
    },
    {
      role: "System Manager", title: "الإدارة", subtitle: "لوحة قيادة مختصرة للجوال",
      items: [
        { label: "لوحة الإدارة الكاملة", desc: "المؤشرات والربحية والمخاطر", icon: "▦", page: "wafd-one-dashboard", primary: true },
        { label: "التشغيل", desc: "المشاريع والخطط والإنتاج", icon: "⚙", page: "wafd-operations-hub" },
        { label: "المخزون والمشتريات", desc: "المواد والحركات والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "التوصيل", desc: "التحميل والرحلات والتسليم", icon: "➜", page: "wafd-delivery-hub" },
        { label: "تقارير التوصيل", desc: "معاينة ومشاركة وطباعة تقرير الشركة أو الفندق", icon: "▤", page: "wafd-delivery-report" },
        { label: "التسليم الميداني", desc: "بدء الرحلة والتصوير وإثبات التسليم", icon: "📷", page: "wafd-driver-trips" },
        { label: "المالية", desc: "الفواتير والتحصيل", icon: "ر.س", page: "wafd-finance-hub" },
        { label: "إفطار صائم", desc: "الإدارة والفريق والتشغيل اليومي", icon: "☾", page: "wafd-iftar-operations", special: true },
        { label: "متابعة إفطار الصائم", desc: "متابعة الإنتاج والتغليف والتحميل والتوصيل", icon: "◉", page: "wafd-iftar-team" },
        { label: "المستندات والتعهدات", desc: "المستندات والطباعة", icon: "▤", page: "wafd-documents-hub" },
        { label: "إنشاء عرض سعر", desc: "إعداد عرض جديد للعميل", icon: "💼", new_doctype: "WAFD Quotation" },
        { label: "العروض المرسلة", desc: "فقط العروض التي تمت مشاركتها وتسجيل إرسالها", icon: "✓", doctype: "WAFD Quotation", filters: { sent_on: ["is", "set"] } },
        { label: "إدارة الموظفين", desc: "إضافة الحسابات وتحديد المهمات", icon: "♙", page: "wafd-employee-team" }
      ]
    },
    {
      role: "WAFD Operations Manager", title: "مدير العمليات", subtitle: "متابعة التشغيل اليومية",
      items: [
        { label: "لوحة الإدارة الكاملة", desc: "المؤشرات والربحية والمخاطر", icon: "▦", page: "wafd-one-dashboard", primary: true },
        { label: "التشغيل", desc: "المشاريع والخطط والإنتاج", icon: "⚙", page: "wafd-operations-hub" },
        { label: "المخزون والمشتريات", desc: "المواد والحركات والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "التوصيل", desc: "التحميل والرحلات والتسليم", icon: "➜", page: "wafd-delivery-hub" },
        { label: "تقارير التوصيل", desc: "معاينة ومشاركة وطباعة تقرير الشركة أو الفندق", icon: "▤", page: "wafd-delivery-report" },
        { label: "التسليم الميداني", desc: "بدء الرحلة والتصوير وإثبات التسليم", icon: "📷", page: "wafd-driver-trips" },
        { label: "المالية", desc: "الفواتير والتحصيل", icon: "ر.س", page: "wafd-finance-hub" },
        { label: "إفطار صائم", desc: "الإدارة والفريق والتشغيل اليومي", icon: "☾", page: "wafd-iftar-operations", special: true },
        { label: "متابعة إفطار الصائم", desc: "متابعة الإنتاج والتغليف والتحميل والتوصيل", icon: "◉", page: "wafd-iftar-team" },
        { label: "إنشاء عرض سعر", desc: "إعداد عرض جديد للعميل", icon: "💼", new_doctype: "WAFD Quotation" },
        { label: "العروض المرسلة", desc: "فقط العروض التي تمت مشاركتها وتسجيل إرسالها", icon: "✓", doctype: "WAFD Quotation", filters: { sent_on: ["is", "set"] } },
        { label: "إدارة الموظفين", desc: "إضافة الحسابات وتحديد المهمات", icon: "♙", page: "wafd-employee-team" }
      ]
    },
    {
      role: "WAFD Project Manager", title: "مدير المشروع", subtitle: "إدارة المشروع والتخطيط والمتابعة",
      items: [
        { label: "المشاريع", desc: "المشاريع المسندة وحالتها", icon: "◆", doctype: "WAFD Catering Project", primary: true },
        { label: "الخطط اليومية", desc: "الكميات والفنادق اليومية", icon: "◫", doctype: "WAFD Daily Meal Plan" },
        { label: "التشغيل", desc: "الإنتاج والجودة والتغليف", icon: "⚙", page: "wafd-operations-hub" },
        { label: "التوصيل", desc: "الرحلات والتسليم والاستلام", icon: "➜", page: "wafd-delivery-hub" },
        { label: "المستندات", desc: "التعهدات والمستندات التشغيلية", icon: "▤", page: "wafd-documents-hub" },
        { label: "إنشاء عرض سعر", desc: "إعداد عرض جديد للعميل", icon: "💼", new_doctype: "WAFD Quotation" },
        { label: "العروض المرسلة", desc: "فقط العروض التي تمت مشاركتها وتسجيل إرسالها", icon: "✓", doctype: "WAFD Quotation", filters: { sent_on: ["is", "set"] } },
        { label: "إفطار صائم", desc: "المشروع والفريق والتقارير اليومية", icon: "☾", page: "wafd-iftar-operations", special: true },
        { label: "متابعة إفطار الصائم", desc: "متابعة مراحل المشروع لحظة بلحظة", icon: "◉", page: "wafd-iftar-team" }
      ]
    },
    {
      role: "WAFD Production Supervisor", title: "مشرف الإنتاج", subtitle: "الخطة والإنتاج والتغليف",
      items: [
        { label: "دفعات الإنتاج", desc: "تنفيذ ومتابعة دفعات الإنتاج", icon: "▦", doctype: "WAFD Production Batch", primary: true },
        { label: "الخطط اليومية", desc: "الكميات المطلوب إنتاجها", icon: "◫", doctype: "WAFD Daily Meal Plan" },
        { label: "سجلات التغليف", desc: "متابعة الكميات المعبأة", icon: "□", doctype: "WAFD Packaging Record" },
        { label: "الوصفات", desc: "مراجع الوصفات المعتمدة", icon: "≡", doctype: "WAFD Recipe" }
      ]
    },
    {
      role: "WAFD Quality Inspector", title: "مفتش الجودة", subtitle: "الفحص ونقاط التحكم الحرجة",
      items: [
        { label: "فحص الجودة", desc: "الفحوصات المطلوبة ونتائجها", icon: "✓", doctype: "WAFD Quality Inspection", primary: true },
        { label: "دفعات الإنتاج", desc: "دفعات الإنتاج المطلوب فحصها", icon: "▦", doctype: "WAFD Production Batch" },
        { label: "فحوص CCP", desc: "نقاط التحكم الحرجة", icon: "◎", doctype: "WAFD CCP Check" },
        { label: "سجلات التغليف", desc: "قراءة السجلات بعد الفحص", icon: "□", doctype: "WAFD Packaging Record" }
      ]
    },
    {
      role: "WAFD Storekeeper", title: "أمين المستودع", subtitle: "ثلاث مهام عملية للمخزون",
      items: [
        { label: "استلام وتوزيع المشتريات", desc: "إدخال المواد في المستودعات والثلاجات بسهولة", icon: "＋", action: "storekeeper_receive", page: "wafd-storekeeper-home", primary: true },
        { label: "تسليم مواد للموظفين", desc: "اختيار الوظيفة والاسم والمستودع ثم المواد", icon: "➜", action: "storekeeper_handover", page: "wafd-storekeeper-home" },
        { label: "معلومات المخزون", desc: "الأرصدة والنواقص وتنبيهات انتهاء الصلاحية", icon: "▣", action: "storekeeper_inventory", page: "wafd-storekeeper-home" }
      ]
    },
    {
      role: "WAFD Cleaning Supervisor", title: "مشرف النظافة", subtitle: "مواد النظافة المصروفة لك فقط",
      items: [
        { label: "استلام وصرف مواد النظافة", desc: "تأكيد الاستلام وتسجيل المواد المستخدمة من شاشة واحدة", icon: "✓", page: "wafd-cleaning-home", primary: true }
      ]
    },
    {
      role: "WAFD Delivery Supervisor", title: "مشرف التوصيل", subtitle: "خطة التوصيل والمواقع والسائقون",
      items: [
        { label: "إدارة التوصيل", desc: "إنشاء الرحلات والجداول ومتابعة التسليم", icon: "➜", page: "wafd-delivery-supervisor", primary: true },
        { label: "المواقع والفنادق", desc: "إضافة فندق أو مسجد أو موقع إفطار صائم", icon: "⌖", action: "delivery_locations", page: "wafd-delivery-supervisor" },
        { label: "تقارير التوصيل", desc: "معاينة ومشاركة وطباعة تقرير الشركة أو الفندق", icon: "▤", page: "wafd-delivery-report" },
        { label: "مهام إفطار الصائم", desc: "استلام الكمية وتوزيعها على السيارات", icon: "☾", page: "wafd-iftar-team" }
      ]
    },
    {
      role: "WAFD Iftar Kitchen Supervisor", title: "مشرف مطبخ إفطار الصائم", subtitle: "الإنتاج والتغليف والتحميل اليومي",
      items: [
        { label: "مهمة إفطار الصائم", desc: "اعتماد الإنتاج ثم التغليف ثم التحميل", icon: "☾", page: "wafd-iftar-team", primary: true }
      ]
    },
    {
      role: "WAFD Iftar Site Manager", title: "مدير موقع إفطار الصائم", subtitle: "الاستلام والفحص وتسليم المشرفين واعتماد التقارير",
      items: []
    },
    {
      role: "WAFD Iftar Supervisor", title: "مشرف سفر إفطار الصائم", subtitle: "السفر والمساعدون والتوزيع والتوثيق",
      items: []
    },
    {
      role: "WAFD Driver", title: "السائق", subtitle: "رحلاتك المسندة لك فقط",
      items: [
        { label: "رحلاتي", desc: "المركبة والوجهة وحالة الرحلة", icon: "➜", page: "wafd-driver-trips", primary: true }
      ]
    },
    {
      role: "WAFD Delivery Viewer", title: "متابعة التسليم", subtitle: "بيانات الرحلات المسندة لحسابك",
      items: [
        { label: "بيانات التسليم", desc: "عرض الرحلات المسندة وصور التسليم للقراءة فقط", icon: "▤", page: "wafd-delivery-viewer", primary: true },
        { label: "متابعة إفطار الصائم", desc: "متابعة مراحل المشروع للقراءة فقط", icon: "☾", page: "wafd-iftar-team" }
      ]
    },
    {
      role: "WAFD Finance User", title: "المالية", subtitle: "الفوترة والتحصيل والعقود المرجعية",
      items: [
        { label: "الفواتير", desc: "المستحقات وحالة الفواتير", icon: "ر.س", doctype: "WAFD Invoice", primary: true },
        { label: "التحصيل", desc: "الدفعات وربطها بالفواتير", icon: "✓", doctype: "WAFD Payment" },
        { label: "العقود", desc: "المرجع المالي للعقود", icon: "▤", doctype: "WAFD Contract" },
        { label: "عروض الأسعار", desc: "مراجعة الأسعار والإجماليات", icon: "💼", doctype: "WAFD Quotation" },
        { label: "المشاريع", desc: "المشروع المرتبط بالفاتورة", icon: "◆", doctype: "WAFD Catering Project" }
      ]
    },
    {
      role: "WAFD Approver", title: "المعتمد", subtitle: "المراجعة والاعتماد المالي",
      items: [
        { label: "المالية", desc: "الفواتير والتحصيل والمراجعة", icon: "ر.س", page: "wafd-finance-hub", primary: true },
        { label: "طلبات الاعتماد", desc: "الطلبات التي تحتاج قرارًا", icon: "✓", doctype: "WAFD Approval Request" },
        { label: "عروض الأسعار", desc: "مراجعة واعتماد عروض الأسعار", icon: "💼", doctype: "WAFD Quotation" }
      ]
    },
    {
      role: "WAFD Auditor", title: "المدقق", subtitle: "مراجعة السجلات المالية",
      items: [
        { label: "الفواتير", desc: "مراجعة الفواتير", icon: "ر.س", doctype: "WAFD Invoice", primary: true },
        { label: "التحصيل", desc: "مراجعة التحصيلات", icon: "✓", doctype: "WAFD Payment" },
        { label: "عروض الأسعار", desc: "مراجعة سجل عروض الأسعار", icon: "💼", doctype: "WAFD Quotation" },
        { label: "المالية", desc: "مركز المراجعة المالية", icon: "▦", page: "wafd-finance-hub" }
      ]
    }
  ];

  const matchedProfiles = profiles.filter((candidate) => roles.has(candidate.role));
  let profile;
  if (isExecutive) {
    profile = matchedProfiles.find((candidate) => candidate.role === "System Manager") || matchedProfiles.find((candidate) => candidate.role === "WAFD Operations Manager");
  } else if (matchedProfiles.length > 1) {
    const seen = new Set();
    const mergedItems = [];
    matchedProfiles.forEach((candidate) => (candidate.items || []).forEach((item) => {
      const key = [item.page || "", item.doctype || "", item.new_doctype || "", item.action || "", item.label || ""].join("|");
      if (!seen.has(key)) {
        seen.add(key);
        mergedItems.push(item);
      }
    }));
    profile = {role: "Multiple Tasks", title: "مهام متعددة", subtitle: "الأدوات المصرح بها حسب المهمات المسندة", items: mergedItems};
  } else {
    profile = matchedProfiles[0];
  }
  profile = profile || {role: "Desk User", title: "WAFD ONE", subtitle: "لا توجد أدوات تشغيلية مخصصة لهذا الحساب", items: []};
  const isolatedFieldRoles = new Set(["WAFD Driver", "WAFD Cleaning Supervisor", "WAFD Delivery Viewer"]);
  const isolatedFieldProfile = matchedProfiles.length > 0 && matchedProfiles.every((candidate) => isolatedFieldRoles.has(candidate.role));
  const driverOfflineProfile = roles.has("WAFD Driver") && isolatedFieldProfile;
  const DRIVER_OFFLINE_DB_NAME = "wafd_driver_offline_rc293";
  const DRIVER_OFFLINE_STATE_KEY = `driver:${frappe.session.user || "Guest"}`;
  let driverOfflineDbPromise = null;
  let driverHomeSyncing = false;

  function openDriverOfflineDb() {
    if (driverOfflineDbPromise) return driverOfflineDbPromise;
    driverOfflineDbPromise = new Promise((resolve, reject) => {
      if (!window.indexedDB) return reject(new Error("IndexedDB unavailable"));
      const request = indexedDB.open(DRIVER_OFFLINE_DB_NAME, 1);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains("state")) db.createObjectStore("state", {keyPath:"key"});
        if (!db.objectStoreNames.contains("queue")) db.createObjectStore("queue", {keyPath:"id"});
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("IndexedDB open failed"));
    });
    return driverOfflineDbPromise;
  }

  async function driverDbRequest(storeName, mode, operation) {
    const db = await openDriverOfflineDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, mode);
      const request = operation(tx.objectStore(storeName));
      let result;
      let settled = false;
      const finish = (value) => { if (!settled) { settled = true; resolve(value); } };
      const fail = (error) => { if (!settled) { settled = true; reject(error); } };
      request.onsuccess = () => { result = request.result; if (mode === "readonly") finish(result); };
      request.onerror = () => fail(request.error || new Error("IndexedDB request failed"));
      tx.oncomplete = () => finish(result);
      tx.onabort = () => fail(tx.error || new Error("IndexedDB transaction aborted"));
      tx.onerror = () => fail(tx.error || new Error("IndexedDB transaction failed"));
    });
  }

  async function driverPendingActions() {
    const rows = await driverDbRequest("queue", "readonly", store => store.getAll());
    return (rows || []).filter(row => row.user === (frappe.session.user || "Guest"))
      .sort((a,b) => String(a.created_at || "").localeCompare(String(b.created_at || "")));
  }

  async function updateDriverConnectivity(mode, detail="") {
    if (!driverOfflineProfile) return;
    const $bar = $root.find("#wafd-driver-connectivity");
    if (!$bar.length) return;
    let pending = 0;
    try { pending = (await driverPendingActions()).length; } catch (_error) {}
    const offline = mode === "offline" || !navigator.onLine;
    let label = detail;
    if (!label) {
      if (mode === "syncing") label = uiLang === "ar" ? "جارٍ مزامنة العمليات المحفوظة…" : "Syncing saved actions…";
      else if (mode === "error") label = uiLang === "ar" ? "تعذر إكمال المزامنة — ستتم إعادة المحاولة تلقائياً" : "Sync is pending — it will retry automatically";
      else if (offline) label = uiLang === "ar" ? "دون إنترنت — يمكنك العمل من رحلاتي المحفوظة" : "Offline — you can work from My Trips saved on this phone";
      else label = uiLang === "ar" ? "متصل — الرحلات والمزامنة جاهزة" : "Online — trips and sync are ready";
    }
    if (pending) label += uiLang === "ar" ? ` — ${pending} بانتظار المزامنة` : ` — ${pending} waiting to sync`;
    $bar.removeClass("is-offline is-syncing is-error")
      .addClass(mode === "syncing" ? "is-syncing" : mode === "error" ? "is-error" : offline ? "is-offline" : "is-online")
      .find("span").text(label);
  }

  async function preloadDriverOfflineData() {
    if (!driverOfflineProfile) return;
    if (!navigator.onLine) { await updateDriverConnectivity("offline"); return; }
    if (driverHomeSyncing) return;
    driverHomeSyncing = true;
    await updateDriverConnectivity("syncing");
    try {
      const pending = await driverPendingActions();
      for (const row of pending) {
        await frappe.call({
          method:"wafd_one.driver_portal.sync_offline_driver_action",
          args:{trip_name:row.trip_name, action:row.action, captured_at:row.captured_at, payload:JSON.stringify(row.payload || {})},
          freeze:false,
        });
        await driverDbRequest("queue", "readwrite", store => store.delete(row.id));
      }
      const response = await frappe.call({method:"wafd_one.driver_portal.list_my_trips", freeze:false});
      const message = response.message || {};
      await driverDbRequest("state", "readwrite", store => store.put({
        key:DRIVER_OFFLINE_STATE_KEY,
        user:frappe.session.user || "Guest",
        trips:message.trips || [],
        hiddenUpcomingCount:Number(message.hidden_upcoming_count || 0),
        emptyReason:message.empty_reason || null,
        emptyDetail:message.reconciliation?.blocked?.[0]?.message || "",
        saved_at:new Date().toISOString(),
      }));
      await updateDriverConnectivity("online", uiLang === "ar" ? "متصل — تم تحديث الرحلات وحفظها على الهاتف" : "Online — trips updated and saved on this phone");
    } catch (_error) {
      await updateDriverConnectivity(navigator.onLine ? "error" : "offline");
    } finally {
      driverHomeSyncing = false;
    }
  }


  function openNewHotelDialog() {
    const dialog = new frappe.ui.Dialog({
      title: __("إضافة فندق جديد / New Hotel"),
      fields: [
        {fieldname:"hotel_name", fieldtype:"Data", label:__("اسم الفندق بالعربي / Arabic Hotel Name"), reqd:1},
        {fieldname:"hotel_name_en", fieldtype:"Data", label:__("اسم الفندق بالإنجليزي / English Hotel Name"), reqd:1},
        {fieldname:"district", fieldtype:"Data", label:__("الحي / District")}
      ],
      primary_action_label: __("حفظ الفندق / Save Hotel"),
      primary_action: async (values) => {
        dialog.get_primary_btn().prop("disabled", true);
        try {
          const r = await frappe.call({
            method:"wafd_one.wafd_one.doctype.wafd_hotel.wafd_hotel.create_hotel_for_undertaking",
            args: values,
            freeze:true,
            freeze_message: __("جارٍ حفظ الفندق...")
          });
          dialog.hide();
          frappe.show_alert({
            message: r.message?.created ? __("تمت إضافة الفندق بنجاح") : __("الفندق موجود بالفعل"),
            indicator:"green"
          }, 4);
        } finally {
          dialog.get_primary_btn().prop("disabled", false);
        }
      }
    });
    dialog.show();
  }

  function canRead(item) {
    if (!item.doctype) return true;
    try { return !frappe.model.can_read || frappe.model.can_read(item.doctype); }
    catch (e) { return true; }
  }

  const items = (profile.items || []).filter(canRead);

  function renderRoleHome() {
    $root.attr("dir", rtl() ? "rtl" : "ltr");
    const roleLabel = tr(profile.title);
    const escapedUser = frappe.utils.escape_html(currentUser);
    const escapedRole = frappe.utils.escape_html(roleLabel);
    $root.html(`
      <div class="wafd-role-home">
        <section class="wafd-pwa-appbar" aria-label="WAFD ONE">
          <button type="button" class="wafd-pwa-menu-btn" aria-label="القائمة" aria-expanded="false">
            <span></span><span></span><span></span>
          </button>
          <strong>WAFD ONE</strong>
          <div class="wafd-pwa-menu" role="menu" hidden>
            ${isolatedFieldProfile ? "" : `<button type="button" data-action="home">⌂ <span>${tr("الرئيسية")}</span></button>`}
            <label class="wafd-pwa-language-row" for="wafd-pwa-language">
              <span>文 ${tr("اللغة") || "Language"}</span>
              <select id="wafd-pwa-language" aria-label="${tr("اللغة") || "Language"}">${Object.entries(LANGS).map(([k,v])=>`<option value="${k}" ${k===uiLang?"selected":""}>${v}</option>`).join("")}</select>
            </label>
            ${isolatedFieldProfile ? "" : `<div class="wafd-pwa-account"><small>${tr("المستخدم")}</small><b>${escapedUser}</b></div>`}
            <button type="button" class="is-danger" data-action="logout">↪ <span>${tr("تسجيل الخروج")}</span></button>
          </div>
        </section>
        <section class="wafd-mobile-hero">
          <div class="wafd-mobile-brand">
            <div class="wafd-mobile-logo"><img src="/assets/wafd_one/images/wafd-almadinah-dashboard.png" alt="WAFD ONE"></div>
            <div><span>${uiLang==='ar'?'شركة وفد المدينة لخدمات الإعاشة':'Wafd Al Madinah Catering Services'}</span><h1>WAFD ONE</h1></div>
          </div>
          <div class="wafd-mobile-user">
            <div><small>${tr("المستخدم")}</small><strong>${escapedUser}</strong></div>
            <div><small>${tr("الدور")}</small><strong>${escapedRole}</strong></div>
            <div><small>${tr("التاريخ")}</small><strong>${frappe.utils.escape_html(today)}</strong></div>
          </div>
        </section>
        ${driverOfflineProfile ? `<section class="wafd-driver-connectivity" id="wafd-driver-connectivity" role="status" aria-live="polite"><i></i><span>${navigator.onLine ? (uiLang==='ar'?'متصل — جارٍ تحديث الرحلات':'Online — updating trips') : (uiLang==='ar'?'دون إنترنت — يمكنك العمل من رحلاتي المحفوظة':'Offline — use My Trips saved on this phone')}</span></section>` : ""}
        <section class="wafd-mobile-grid">
          ${items.map((item, idx) => `<button type="button" class="wafd-mobile-card ${item.primary ? "is-primary" : ""} ${item.special ? "is-special" : ""}" data-idx="${idx}"><b>${item.icon || "•"}</b><span>${frappe.utils.escape_html(tr(item.label || ""))}</span><small>${frappe.utils.escape_html(tr(item.desc || ""))}</small><i>${rtl()?"←":"→"}</i></button>`).join("")}
        </section>
        ${items.length ? "" : `<div class="wafd-mobile-empty">${uiLang==='ar'?'لا توجد أدوات متاحة لهذا الحساب. راجع الدور والصلاحيات مع مسؤول النظام.':'No tools are available for this account. Please review the assigned role and permissions.'}</div>`}
      </div>`);

    const $pwaMenu = $root.find(".wafd-pwa-menu");
    const $pwaMenuBtn = $root.find(".wafd-pwa-menu-btn");
    const closePwaMenu = () => {
      $pwaMenu.attr("hidden", true);
      $pwaMenuBtn.attr("aria-expanded", "false");
    };
    $pwaMenuBtn.on("click", function (event) {
      event.stopPropagation();
      const willOpen = $pwaMenu.attr("hidden") !== undefined;
      if (willOpen) {
        $pwaMenu.removeAttr("hidden");
        $pwaMenuBtn.attr("aria-expanded", "true");
      } else {
        closePwaMenu();
      }
    });
    $pwaMenu.on("click", "[data-action]", function () {
      const action = $(this).attr("data-action");
      if (action === "home") {
        closePwaMenu();
        frappe.set_route("wafd-role-home");
        return;
      }
      if (action === "logout") {
        closePwaMenu();
        if (frappe.app?.logout) {
          frappe.app.logout();
        } else {
          window.location.assign("/?cmd=web_logout");
        }
      }
    });
    $(document).off("click.wafdPwaMenu").on("click.wafdPwaMenu", function (event) {
      if (!$(event.target).closest(".wafd-pwa-appbar").length) closePwaMenu();
    });

    $root.find("#wafd-pwa-language").on("change", async function(){
      uiLang=this.value;
      localStorage.setItem("wafd_lang",uiLang);
      document.documentElement.lang=uiLang;
      document.documentElement.dir=rtl()?"rtl":"ltr";
      if (driverOfflineProfile && !navigator.onLine) {
        renderRoleHome();
        await updateDriverConnectivity("offline");
        return;
      }
      await frappe.call({method:"wafd_one.language.set_user_language",args:{language:uiLang},freeze:true,freeze_message:tr("اللغة")+"…"});
      window.location.reload();
    });
    $root.find(".wafd-mobile-card").on("click", function () {
      const item = items[Number($(this).attr("data-idx"))]; if (!item) return;
      if (["storekeeper_receive", "storekeeper_handover", "storekeeper_inventory"].includes(item.action)) {
        localStorage.setItem("wafd_storekeeper_action", item.action.replace("storekeeper_", ""));
        frappe.set_route("wafd-storekeeper-home");
        return;
      }
      if (["delivery_new", "delivery_delivered", "delivery_locations"].includes(item.action)) {
        localStorage.setItem("wafd_delivery_action", item.action.replace("delivery_", ""));
        frappe.set_route("wafd-delivery-supervisor");
        return;
      }
      if (item.page) { frappe.set_route(item.page); return; }
      if (item.action === "new_hotel") { openNewHotelDialog(); return; }
      if (item.new_doctype) {
        // RC210: open the full unsaved form directly. Quick Entry saves in a
        // dialog then closes back to the previous route, which forced the
        // officer to return to home/list and reopen the undertaking. Keeping
        // the document in the full Form means Save -> Preview happens in one
        // continuous workflow on the same record.
        frappe.model.with_doctype(item.new_doctype, () => {
          const doc = frappe.model.get_new_doc(item.new_doctype);
          Object.assign(doc, item.defaults || {});
          frappe.set_route("Form", item.new_doctype, doc.name);
        });
        return;
      }
      if (item.doctype) frappe.set_route("List", item.doctype, item.filters || {});
    });
  }
  renderRoleHome();
  if (driverOfflineProfile) {
    window.addEventListener("offline", () => updateDriverConnectivity("offline"));
    window.addEventListener("online", () => preloadDriverOfflineData());
    window.addEventListener("wafd-driver-connectivity", (event) => {
      const mode = event?.detail?.online === false ? "offline" : "online";
      updateDriverConnectivity(mode);
    });
    if (navigator.storage?.persist) navigator.storage.persist().catch(()=>{});
    wrapper.wafdPreloadDriverOffline = preloadDriverOfflineData;
    preloadDriverOfflineData();
  }

};


// RC217: Frappe can revisit an already-loaded Page without re-running on_page_load.
frappe.pages["wafd-role-home"].on_page_show = function (wrapper) {
  document.body.classList.add("wafd-at-role-home");
  document.getElementById("wafd-global-mobile-back")?.remove();
  document.getElementById("wafd-mobile-back-v218")?.remove();
  document.getElementById("wafd-mobile-back-v219")?.remove();
  setTimeout(() => { document.getElementById("wafd-global-mobile-back")?.remove(); document.getElementById("wafd-mobile-back-v218")?.remove();
  document.getElementById("wafd-mobile-back-v219")?.remove(); }, 120);
  if (typeof wrapper?.wafdPreloadDriverOffline === "function") wrapper.wafdPreloadDriverOffline();
};
