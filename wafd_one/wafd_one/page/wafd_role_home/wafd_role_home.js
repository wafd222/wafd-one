frappe.pages["wafd-role-home"].on_page_load = function (wrapper) {
  $(wrapper).addClass("wafd-role-home-page");
  const roles = new Set(frappe.user_roles || []);
  const isExecutive = roles.has("System Manager") || roles.has("WAFD Operations Manager");
  const isMobile = window.matchMedia("(max-width: 900px)").matches;

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
    "المالية":{en:"Finance",id:"Keuangan",ur:"مالیات",hi:"वित्त",bn:"অর্থ",fr:"Finance",ha:"Kuɗi",sw:"Fedha",uz:"Moliya"},
    "المعتمد":{en:"Approver",id:"Penyetuju",ur:"منظور کنندہ",hi:"अनुमोदक",bn:"অনুমোদনকারী",fr:"Approbateur",ha:"Mai Amincewa",sw:"Muidhinishaji",uz:"Tasdiqlovchi"},
    "المدقق":{en:"Auditor",id:"Auditor",ur:"آڈیٹر",hi:"ऑडिटर",bn:"নিরীক্ষক",fr:"Auditeur",ha:"Mai Bincike",sw:"Mkaguzi",uz:"Auditor"},
    "لوحة الإدارة الكاملة":{en:"Full Management Dashboard",id:"Dasbor Manajemen Lengkap",ur:"مکمل انتظامی ڈیش بورڈ",hi:"पूर्ण प्रबंधन डैशबोर्ड",bn:"সম্পূর্ণ ব্যবস্থাপনা ড্যাশবোর্ড",fr:"Tableau de bord complet",ha:"Cikakken Dashboard",sw:"Dashibodi Kamili",uz:"To‘liq boshqaruv paneli"},
    "التشغيل":{en:"Operations",id:"Operasional",ur:"آپریشنز",hi:"संचालन",bn:"অপারেশন",fr:"Opérations",ha:"Ayyuka",sw:"Uendeshaji",uz:"Operatsiyalar"},
    "المخزون والمشتريات":{en:"Inventory & Purchasing",id:"Stok & Pembelian",ur:"اسٹاک اور خریداری",hi:"स्टॉक और खरीद",bn:"স্টক ও ক্রয়",fr:"Stock & Achats",ha:"Kaya & Saye",sw:"Stoo & Ununuzi",uz:"Ombor & Xarid"},
    "التوصيل":{en:"Delivery",id:"Pengiriman",ur:"ترسیل",hi:"डिलीवरी",bn:"ডেলিভারি",fr:"Livraison",ha:"Isarwa",sw:"Usafirishaji",uz:"Yetkazib berish"},
    "إفطار صائم":{en:"Iftar Saim",id:"Iftar Saim",ur:"افطار صائم",hi:"इफ्तार साइम",bn:"ইফতার সায়েম",fr:"Iftar Saim",ha:"Iftar Saim",sw:"Iftar Saim",uz:"Iftar Saim"},
    "المستندات والتعهدات":{en:"Documents & Undertakings",id:"Dokumen & Pernyataan",ur:"دستاویزات و تعہدات",hi:"दस्तावेज़ और प्रतिज्ञाएँ",bn:"নথি ও অঙ্গীকার",fr:"Documents & Engagements",ha:"Takardu",sw:"Nyaraka",uz:"Hujjatlar"},
    "المشاريع":{en:"Projects",id:"Proyek",ur:"منصوبے",hi:"परियोजनाएँ",bn:"প্রকল্প",fr:"Projets",ha:"Ayyuka",sw:"Miradi",uz:"Loyihalar"},
    "الخطط اليومية":{en:"Daily Plans",id:"Rencana Harian",ur:"روزانہ منصوبے",hi:"दैनिक योजनाएँ",bn:"দৈনিক পরিকল্পনা",fr:"Plans quotidiens",ha:"Tsare-tsaren Yau",sw:"Mipango ya Kila Siku",uz:"Kunlik rejalar"},
    "المستندات":{en:"Documents",id:"Dokumen",ur:"دستاویزات",hi:"दस्तावेज़",bn:"নথি",fr:"Documents",ha:"Takardu",sw:"Nyaraka",uz:"Hujjatlar"},
    "دفعات الإنتاج":{en:"Production Batches",id:"Batch Produksi",ur:"پروڈکشن بیچز",hi:"उत्पादन बैच",bn:"উৎপাদন ব্যাচ",fr:"Lots de production",ha:"Rukunin Samarwa",sw:"Makundi ya Uzalishaji",uz:"Ishlab chiqarish partiyalari"},
    "سجلات التغليف":{en:"Packaging Records",id:"Catatan Pengemasan",ur:"پیکنگ ریکارڈز",hi:"पैकेजिंग रिकॉर्ड",bn:"প্যাকেজিং রেকর্ড",fr:"Registres d’emballage",ha:"Bayanan Marufi",sw:"Rekodi za Ufungashaji",uz:"Qadoqlash yozuvlari"},
    "الوصفات":{en:"Recipes",id:"Resep",ur:"ترکیبیں",hi:"रेसिपी",bn:"রেসিপি",fr:"Recettes",ha:"Girke-girke",sw:"Mapishi",uz:"Retseptlar"},
    "فحص الجودة":{en:"Quality Inspection",id:"Inspeksi Kualitas",ur:"کوالٹی معائنہ",hi:"गुणवत्ता निरीक्षण",bn:"মান পরীক্ষা",fr:"Contrôle qualité",ha:"Duba Inganci",sw:"Ukaguzi wa Ubora",uz:"Sifat tekshiruvi"},
    "فحوص CCP":{en:"CCP Checks",id:"Pemeriksaan CCP",ur:"CCP چیکس",hi:"CCP जांच",bn:"CCP পরীক্ষা",fr:"Contrôles CCP",ha:"Binciken CCP",sw:"Ukaguzi wa CCP",uz:"CCP tekshiruvlari"},
    "حركات المخزون":{en:"Stock Movements",id:"Pergerakan Stok",ur:"اسٹاک موومنٹس",hi:"स्टॉक मूवमेंट",bn:"স্টক মুভমেন্ট",fr:"Mouvements de stock",ha:"Motsin Kaya",sw:"Mienendo ya Stoo",uz:"Ombor harakatlari"},
    "أرصدة المخزون":{en:"Stock Balances",id:"Saldo Stok",ur:"اسٹاک بیلنس",hi:"स्टॉक बैलेंस",bn:"স্টক ব্যালেন্স",fr:"Soldes de stock",ha:"Ma'aunin Kaya",sw:"Salio la Stoo",uz:"Ombor qoldiqlari"},
    "أوامر الشراء":{en:"Purchase Orders",id:"Pesanan Pembelian",ur:"خریداری آرڈرز",hi:"खरीद आदेश",bn:"ক্রয় আদেশ",fr:"Bons de commande",ha:"Odar Saye",sw:"Oda za Ununuzi",uz:"Xarid buyurtmalari"},
    "مخزون أدوات النظافة":{en:"Cleaning Supplies Stock",id:"Stok Peralatan Kebersihan",ur:"صفائی سامان اسٹاک",hi:"सफाई सामग्री स्टॉक",bn:"পরিচ্ছন্নতা সামগ্রী স্টক",fr:"Stock de nettoyage",ha:"Kayan Tsafta",sw:"Stoo ya Vifaa vya Usafi",uz:"Tozalash vositalari ombori"},
    "المواد المصروفة لي":{en:"Materials Issued to Me",id:"Bahan Dikeluarkan untuk Saya",ur:"مجھے جاری کردہ مواد",hi:"मुझे जारी सामग्री",bn:"আমাকে ইস্যু করা সামগ্রী",fr:"Articles qui me sont attribués",ha:"Kayan da aka ba ni",sw:"Vifaa Nilivyopewa",uz:"Menga berilgan materiallar"},
    "رحلات التوصيل":{en:"Delivery Trips",id:"Perjalanan Pengiriman",ur:"ڈیلیوری ٹرپس",hi:"डिलीवरी यात्राएँ",bn:"ডেলিভারি ট্রিপ",fr:"Trajets de livraison",ha:"Tafiyar Isarwa",sw:"Safari za Usafirishaji",uz:"Yetkazib berish safarlari"},
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
      role: "System Manager", title: "الإدارة", subtitle: "لوحة قيادة مختصرة للجوال",
      items: [
        { label: "لوحة الإدارة الكاملة", desc: "المؤشرات والربحية والمخاطر", icon: "▦", page: "wafd-one-dashboard", primary: true },
        { label: "التشغيل", desc: "المشاريع والخطط والإنتاج", icon: "⚙", page: "wafd-operations-hub" },
        { label: "المخزون والمشتريات", desc: "المواد والحركات والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "التوصيل", desc: "التحميل والرحلات والتسليم", icon: "➜", page: "wafd-delivery-hub" },
        { label: "المالية", desc: "الفواتير والتحصيل", icon: "ر.س", page: "wafd-finance-hub" },
        { label: "إفطار صائم", desc: "المشاريع الموسمية والتشغيل اليومي", icon: "☾", page: "wafd-iftar-operations", special: true },
        { label: "المستندات والتعهدات", desc: "المستندات والطباعة", icon: "▤", page: "wafd-documents-hub" },
        { label: "فريق التعهدات", desc: "إضافة وإدارة موظفي التعهدات", icon: "♙", page: "wafd-undertaking-team" }
      ]
    },
    {
      role: "WAFD Operations Manager", title: "مدير العمليات", subtitle: "متابعة التشغيل اليومية",
      items: [
        { label: "لوحة الإدارة الكاملة", desc: "المؤشرات والربحية والمخاطر", icon: "▦", page: "wafd-one-dashboard", primary: true },
        { label: "التشغيل", desc: "المشاريع والخطط والإنتاج", icon: "⚙", page: "wafd-operations-hub" },
        { label: "المخزون والمشتريات", desc: "المواد والحركات والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "التوصيل", desc: "التحميل والرحلات والتسليم", icon: "➜", page: "wafd-delivery-hub" },
        { label: "المالية", desc: "الفواتير والتحصيل", icon: "ر.س", page: "wafd-finance-hub" },
        { label: "إفطار صائم", desc: "المشاريع الموسمية والتشغيل اليومي", icon: "☾", page: "wafd-iftar-operations", special: true },
        { label: "فريق التعهدات", desc: "إضافة وإدارة موظفي التعهدات", icon: "♙", page: "wafd-undertaking-team" }
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
        { label: "إفطار صائم", desc: "المشاريع الموسمية", icon: "☾", page: "wafd-iftar-operations", special: true }
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
      role: "WAFD Storekeeper", title: "أمين المستودع", subtitle: "المخزون والاستلام والصرف",
      items: [
        { label: "حركات المخزون", desc: "استلام وصرف وتحويل المواد", icon: "↔", doctype: "WAFD Stock Movement", primary: true },
        { label: "أرصدة المخزون", desc: "الكميات المتاحة بالمستودعات", icon: "▥", doctype: "WAFD Stock Balance" },
        { label: "المخزون والمشتريات", desc: "كل أدوات المستودع والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "أوامر الشراء", desc: "متابعة المواد المشتراة", icon: "⌑", doctype: "WAFD Purchase Order" },
        { label: "إفطار صائم", desc: "المخزون المرتبط بالمشاريع الموسمية", icon: "☾", page: "wafd-iftar-operations", special: true }
      ]
    },
    {
      role: "WAFD Cleaning Supervisor", title: "مشرف النظافة", subtitle: "مواد النظافة المصروفة لك فقط",
      items: [
        { label: "مخزون أدوات النظافة", desc: "رصيد مستودع أدوات النظافة", icon: "✦", doctype: "WAFD Stock Balance", filters: { warehouse: "مستودع 7 - أدوات النظافة" }, primary: true },
        { label: "المواد المصروفة لي", desc: "حركات الصرف المسندة لحسابك", icon: "▤", doctype: "WAFD Stock Movement" }
      ]
    },
    {
      role: "WAFD Delivery Supervisor", title: "مشرف التوصيل", subtitle: "التحميل والرحلات والتسليم",
      items: [
        { label: "رحلات التوصيل", desc: "إدارة ومتابعة الرحلات", icon: "➜", doctype: "WAFD Delivery Trip", primary: true },
        { label: "سجلات التحميل", desc: "التحميل قبل خروج الرحلة", icon: "▣", doctype: "WAFD Loading Record" },
        { label: "سندات التسليم", desc: "التسليم للجهة المستفيدة", icon: "▤", doctype: "WAFD Delivery Note" },
        { label: "سندات الاستلام", desc: "توثيق الاستلام النهائي", icon: "✓", doctype: "WAFD Receiving Note" },
        { label: "إفطار صائم", desc: "التوصيل للمشاريع الموسمية", icon: "☾", page: "wafd-iftar-operations", special: true }
      ]
    },
    {
      role: "WAFD Driver", title: "السائق", subtitle: "رحلاتك المسندة لك فقط",
      items: [
        { label: "رحلاتي", desc: "المركبة والوجهة وحالة الرحلة", icon: "➜", doctype: "WAFD Delivery Trip", primary: true }
      ]
    },
    {
      role: "WAFD Finance User", title: "المالية", subtitle: "الفوترة والتحصيل والعقود المرجعية",
      items: [
        { label: "الفواتير", desc: "المستحقات وحالة الفواتير", icon: "ر.س", doctype: "WAFD Invoice", primary: true },
        { label: "التحصيل", desc: "الدفعات وربطها بالفواتير", icon: "✓", doctype: "WAFD Payment" },
        { label: "العقود", desc: "المرجع المالي للعقود", icon: "▤", doctype: "WAFD Contract" },
        { label: "المشاريع", desc: "المشروع المرتبط بالفاتورة", icon: "◆", doctype: "WAFD Catering Project" }
      ]
    },
    {
      role: "WAFD Approver", title: "المعتمد", subtitle: "المراجعة والاعتماد المالي",
      items: [
        { label: "المالية", desc: "الفواتير والتحصيل والمراجعة", icon: "ر.س", page: "wafd-finance-hub", primary: true },
        { label: "طلبات الاعتماد", desc: "الطلبات التي تحتاج قرارًا", icon: "✓", doctype: "WAFD Approval Request" }
      ]
    },
    {
      role: "WAFD Auditor", title: "المدقق", subtitle: "مراجعة السجلات المالية",
      items: [
        { label: "الفواتير", desc: "مراجعة الفواتير", icon: "ر.س", doctype: "WAFD Invoice", primary: true },
        { label: "التحصيل", desc: "مراجعة التحصيلات", icon: "✓", doctype: "WAFD Payment" },
        { label: "المالية", desc: "مركز المراجعة المالية", icon: "▦", page: "wafd-finance-hub" }
      ]
    }
  ];

  const preferredRole = (!isExecutive && roles.has("WAFD Undertaking Officer")) ? "WAFD Undertaking Officer" : ((!isExecutive && roles.has("WAFD Undertaking Reviewer")) ? "WAFD Undertaking Reviewer" : null);
  const profile = (preferredRole ? profiles.find((candidate) => candidate.role === preferredRole) : profiles.find((candidate) => roles.has(candidate.role))) || {
    role: "Desk User", title: "WAFD ONE", subtitle: "لا توجد أدوات تشغيلية مخصصة لهذا الحساب", items: []
  };

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
        <section class="wafd-mobile-hero">
          <div class="wafd-mobile-lang"><label>${tr("اللغة") || "Language"}</label><select id="wafd-role-lang">${Object.entries(LANGS).map(([k,v])=>`<option value="${k}" ${k===uiLang?"selected":""}>${v}</option>`).join("")}</select></div>
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
        <section class="wafd-mobile-grid">
          ${items.map((item, idx) => `<button type="button" class="wafd-mobile-card ${item.primary ? "is-primary" : ""} ${item.special ? "is-special" : ""}" data-idx="${idx}"><b>${item.icon || "•"}</b><span>${frappe.utils.escape_html(tr(item.label || ""))}</span><small>${frappe.utils.escape_html(tr(item.desc || ""))}</small><i>${rtl()?"←":"→"}</i></button>`).join("")}
        </section>
        ${items.length ? "" : `<div class="wafd-mobile-empty">${uiLang==='ar'?'لا توجد أدوات متاحة لهذا الحساب. راجع الدور والصلاحيات مع مسؤول النظام.':'No tools are available for this account. Please review the assigned role and permissions.'}</div>`}
      </div>`);

    $root.find("#wafd-role-lang").on("change", function(){uiLang=this.value;localStorage.setItem("wafd_lang",uiLang);renderRoleHome();});
    $root.find(".wafd-mobile-card").on("click", function () {
      const item = items[Number($(this).attr("data-idx"))]; if (!item) return;
      if (item.page) { frappe.set_route(item.page); return; }
      if (item.new_doctype) { frappe.new_doc(item.new_doctype); return; }
      if (item.doctype) frappe.set_route("List", item.doctype, item.filters || {});
    });
  }
  renderRoleHome();

};
