frappe.pages["wafd-driver-trips"].on_page_load = function (wrapper) {
  const roles = new Set(frappe.user_roles || []);
  const managerRoles = ["System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"];
  const isManager = managerRoles.some((role) => roles.has(role));
  if (!roles.has("WAFD Driver") && !isManager) {
    wrapper.innerHTML = "";
    requestAnimationFrame(() => frappe.set_route("wafd-role-home"));
    return;
  }

  const lang = localStorage.getItem("wafd_lang") || "ar";
  const rtl = ["ar", "ur"].includes(lang);
  const T = {
    my_trips:{ar:"رحلاتي",en:"My Trips",id:"Perjalanan Saya",ur:"میری ٹرپس",hi:"मेरी यात्राएँ",bn:"আমার ট্রিপ",fr:"Mes trajets",ha:"Tafiyoyina",sw:"Safari Zangu",uz:"Safarlarim"},
    field_delivery:{ar:"التسليم الميداني",en:"Field Delivery",id:"Pengiriman Lapangan",ur:"فیلڈ ڈیلیوری",hi:"मैदानी डिलीवरी",bn:"মাঠ ডেলিভারি",fr:"Livraison terrain",ha:"Isarwa a fili",sw:"Uwasilishaji wa eneo",uz:"Joydagi yetkazish"},
    back:{ar:"رجوع",en:"Back",id:"Kembali",ur:"واپس",hi:"वापस",bn:"ফিরুন",fr:"Retour",ha:"Baya",sw:"Rudi",uz:"Orqaga"},
    refresh:{ar:"تحديث",en:"Refresh",id:"Muat ulang",ur:"تازہ کریں",hi:"रीफ़्रेश",bn:"রিফ্রেশ",fr:"Actualiser",ha:"Sabunta",sw:"Onyesha upya",uz:"Yangilash"},
    no_trips:{ar:"لا توجد رحلات مسندة إليك حاليًا.",en:"No trips are currently assigned to you.",id:"Saat ini tidak ada perjalanan yang ditugaskan.",ur:"اس وقت آپ کو کوئی ٹرپ تفویض نہیں کیا گیا۔",hi:"अभी आपको कोई यात्रा नहीं सौंपी गई है।",bn:"বর্তমানে আপনাকে কোনো ট্রিপ দেওয়া হয়নি।",fr:"Aucun trajet ne vous est attribué actuellement.",ha:"Babu tafiya da aka ba ka yanzu.",sw:"Hakuna safari uliyopewa kwa sasa.",uz:"Hozir sizga safar biriktirilmagan."},
    no_trips_manager:{ar:"لا توجد رحلات توصيل حالية.",en:"There are no current delivery trips."},
    hotel:{ar:"الوجهة",en:"Destination",id:"Tujuan",ur:"منزل",hi:"गंतव्य",bn:"গন্তব্য",fr:"Destination",ha:"Wurin zuwa",sw:"Mahali",uz:"Manzil"},
    vehicle:{ar:"المركبة",en:"Vehicle",id:"Kendaraan",ur:"گاڑی",hi:"वाहन",bn:"যানবাহন",fr:"Véhicule",ha:"Mota",sw:"Gari",uz:"Transport"},
    driver:{ar:"السائق",en:"Driver",id:"Pengemudi",ur:"ڈرائیور",hi:"चालक",bn:"চালক",fr:"Chauffeur",ha:"Direba",sw:"Dereva",uz:"Haydovchi"},
    quantity:{ar:"الكمية",en:"Quantity",id:"Jumlah",ur:"مقدار",hi:"मात्रा",bn:"পরিমাণ",fr:"Quantité",ha:"Adadi",sw:"Kiasi",uz:"Miqdor"},
    status:{ar:"الحالة",en:"Status",id:"Status",ur:"حالت",hi:"स्थिति",bn:"অবস্থা",fr:"Statut",ha:"Matsayi",sw:"Hali",uz:"Holat"},
    arrival:{ar:"الوصول المخطط",en:"Planned arrival",id:"Tiba terencana",ur:"متوقع آمد",hi:"नियोजित आगमन",bn:"পরিকল্পিত আগমন",fr:"Arrivée prévue",ha:"Lokacin isowa",sw:"Muda wa kuwasili",uz:"Rejalashtirilgan yetib kelish"},
    loading_photo:{ar:"صورة التحميل",en:"Loading photo",id:"Foto pemuatan",ur:"لوڈنگ تصویر",hi:"लोडिंग फ़ोटो",bn:"লোডিং ছবি",fr:"Photo du chargement",ha:"Hoton lodi",sw:"Picha ya upakiaji",uz:"Yuklash rasmi"},
    uploaded_by:{ar:"وثقها",en:"Documented by",id:"Didokumentasikan oleh",ur:"دستاویز کنندہ",hi:"दर्ज करने वाला",bn:"নথিভুক্ত করেছেন",fr:"Documentée par",ha:"Wanda ya tabbatar",sw:"Aliyethibitisha",uz:"Tasdiqlagan"},
    seal:{ar:"رقم الختم",en:"Seal number",id:"Nomor segel",ur:"مہر نمبر",hi:"सील नंबर",bn:"সিল নম্বর",fr:"Numéro de scellé",ha:"Lambar hatimi",sw:"Namba ya muhuri",uz:"Muhr raqami"},
    start:{ar:"استلام الرحلة وبدء التوصيل",en:"Accept & start trip",id:"Terima & mulai perjalanan",ur:"ٹرپ قبول اور شروع کریں",hi:"यात्रा स्वीकार कर शुरू करें",bn:"ট্রিপ গ্রহণ ও শুরু করুন",fr:"Accepter et démarrer",ha:"Karɓa ka fara tafiya",sw:"Kubali na anza safari",uz:"Safarni qabul qilish va boshlash"},
    mark_arrived:{ar:"تسجيل الوصول",en:"Mark arrived",id:"Tandai tiba",ur:"آمد درج کریں",hi:"आगमन दर्ज करें",bn:"আগমন নিশ্চিত করুন",fr:"Enregistrer l’arrivée",ha:"Yi rajistar isowa",sw:"Thibitisha kuwasili",uz:"Yetib kelishni belgilash"},
    proof:{ar:"إثبات التسليم",en:"Delivery proof",id:"Bukti pengiriman",ur:"ڈیلیوری ثبوت",hi:"डिलीवरी प्रमाण",bn:"ডেলিভারি প্রমাণ",fr:"Preuve de livraison",ha:"Tabbacin isarwa",sw:"Uthibitisho wa uwasilishaji",uz:"Yetkazib berish dalili"},
    delivered:{ar:"تم توثيق التسليم",en:"Delivery documented",id:"Pengiriman terdokumentasi",ur:"ڈیلیوری درج ہو گئی",hi:"डिलीवरी दर्ज हो गई",bn:"ডেলিভারি নথিভুক্ত",fr:"Livraison documentée",ha:"An tabbatar da isarwa",sw:"Uwasilishaji umethibitishwa",uz:"Yetkazib berish tasdiqlandi"},
    receiver:{ar:"اسم المستلم",en:"Receiver name",id:"Nama penerima",ur:"وصول کنندہ کا نام",hi:"प्राप्तकर्ता का नाम",bn:"গ্রহীতার নাম",fr:"Nom du destinataire",ha:"Sunan mai karɓa",sw:"Jina la mpokeaji",uz:"Qabul qiluvchi"},
    mobile:{ar:"جوال المستلم (اختياري)",en:"Receiver mobile (optional)",id:"Ponsel penerima (opsional)",ur:"وصول کنندہ کا موبائل (اختیاری)",hi:"प्राप्तकर्ता मोबाइल (वैकल्पिक)",bn:"গ্রহীতার মোবাইল (ঐচ্ছিক)",fr:"Téléphone du destinataire (facultatif)",ha:"Wayar mai karɓa (zaɓi)",sw:"Simu ya mpokeaji (hiari)",uz:"Qabul qiluvchi telefoni (ixtiyoriy)"},
    received:{ar:"الكمية المستلمة",en:"Received quantity",id:"Jumlah diterima",ur:"وصول شدہ مقدار",hi:"प्राप्त मात्रा",bn:"গৃহীত পরিমাণ",fr:"Quantité reçue",ha:"Adadin da aka karɓa",sw:"Kiasi kilichopokelewa",uz:"Qabul qilingan miqdor"},
    rejected:{ar:"الكمية المرفوضة",en:"Rejected quantity",id:"Jumlah ditolak",ur:"مسترد مقدار",hi:"अस्वीकृत मात्रा",bn:"প্রত্যাখ্যাত পরিমাণ",fr:"Quantité refusée",ha:"Adadin da aka ƙi",sw:"Kiasi kilichokataliwa",uz:"Rad etilgan miqdor"},
    acceptance:{ar:"نتيجة الاستلام",en:"Acceptance result",id:"Hasil penerimaan",ur:"وصولی نتیجہ",hi:"स्वीकृति परिणाम",bn:"গ্রহণের ফল",fr:"Résultat de réception",ha:"Sakamakon karɓa",sw:"Matokeo ya kupokea",uz:"Qabul natijasi"},
    full:{ar:"مقبول بالكامل",en:"Fully accepted",id:"Diterima penuh",ur:"مکمل قبول",hi:"पूर्ण स्वीकृत",bn:"সম্পূর্ণ গৃহীত",fr:"Accepté entièrement",ha:"An karɓa gaba ɗaya",sw:"Imekubaliwa yote",uz:"To‘liq qabul qilindi"},
    partial:{ar:"مقبول جزئيًا",en:"Partially accepted",id:"Diterima sebagian",ur:"جزوی قبول",hi:"आंशिक स्वीकृत",bn:"আংশিক গৃহীত",fr:"Accepté partiellement",ha:"An karɓa wani ɓangare",sw:"Imekubaliwa sehemu",uz:"Qisman qabul qilindi"},
    refused:{ar:"مرفوض",en:"Rejected",id:"Ditolak",ur:"مسترد",hi:"अस्वीकृत",bn:"প্রত্যাখ্যাত",fr:"Refusé",ha:"An ƙi",sw:"Imekataliwa",uz:"Rad etildi"},
    quick_note:{ar:"ملاحظة تشغيلية",en:"Operational note",id:"Catatan operasional",ur:"آپریشنل نوٹ",hi:"परिचालन टिप्पणी",bn:"অপারেশন নোট",fr:"Note opérationnelle",ha:"Bayanin aiki",sw:"Dokezo la uendeshaji",uz:"Operatsion izoh"},
    choose:{ar:"بدون ملاحظة محددة",en:"No preset note",id:"Tanpa catatan",ur:"کوئی طے شدہ نوٹ نہیں",hi:"कोई पूर्व टिप्पणी नहीं",bn:"কোনো নির্দিষ্ট নোট নেই",fr:"Aucune note prédéfinie",ha:"Babu zaɓaɓɓen bayani",sw:"Hakuna dokezo maalum",uz:"Tayyor izoh yo‘q"},
    notes:{ar:"ملاحظة إضافية",en:"Additional note",id:"Catatan tambahan",ur:"اضافی نوٹ",hi:"अतिरिक्त टिप्पणी",bn:"অতিরিক্ত নোট",fr:"Note supplémentaire",ha:"Ƙarin bayani",sw:"Dokezo la ziada",uz:"Qo‘shimcha izoh"},
    photo:{ar:"تصوير/اختيار صورة التسليم",en:"Capture/select delivery photo",id:"Ambil/pilih foto pengiriman",ur:"ڈیلیوری تصویر لیں/منتخب کریں",hi:"डिलीवरी फ़ोटो लें/चुनें",bn:"ডেলিভারি ছবি তুলুন/নির্বাচন করুন",fr:"Prendre/choisir la photo",ha:"Ɗauki/zaɓi hoton isarwa",sw:"Piga/chagua picha ya uwasilishaji",uz:"Yetkazish rasmini olish/tanlash"},
    signature:{ar:"توقيع المستلم",en:"Receiver signature",id:"Tanda tangan penerima",ur:"وصول کنندہ کا دستخط",hi:"प्राप्तकर्ता हस्ताक्षर",bn:"গ্রহীতার স্বাক্ষর",fr:"Signature du destinataire",ha:"Sa hannun mai karɓa",sw:"Sahihi ya mpokeaji",uz:"Qabul qiluvchi imzosi"},
    clear:{ar:"مسح التوقيع",en:"Clear signature",id:"Hapus tanda tangan",ur:"دستخط صاف کریں",hi:"हस्ताक्षर मिटाएँ",bn:"স্বাক্ষর মুছুন",fr:"Effacer la signature",ha:"Goge sa hannu",sw:"Futa sahihi",uz:"Imzoni tozalash"},
    submit:{ar:"حفظ إثبات التسليم",en:"Save delivery proof",id:"Simpan bukti pengiriman",ur:"ڈیلیوری ثبوت محفوظ کریں",hi:"डिलीवरी प्रमाण सहेजें",bn:"ডেলিভারি প্রমাণ সংরক্ষণ",fr:"Enregistrer la preuve",ha:"Ajiye tabbacin isarwa",sw:"Hifadhi uthibitisho",uz:"Yetkazish dalilini saqlash"},
    close:{ar:"إغلاق",en:"Close",id:"Tutup",ur:"بند کریں",hi:"बंद करें",bn:"বন্ধ",fr:"Fermer",ha:"Rufe",sw:"Funga",uz:"Yopish"},
    saving:{ar:"جارٍ الحفظ...",en:"Saving...",id:"Menyimpan...",ur:"محفوظ ہو رہا ہے...",hi:"सहेजा जा रहा है...",bn:"সংরক্ষণ হচ্ছে...",fr:"Enregistrement...",ha:"Ana ajiyewa...",sw:"Inahifadhi...",uz:"Saqlanmoqda..."},
    open_map:{ar:"فتح الموقع",en:"Open location",id:"Buka lokasi",ur:"مقام کھولیں",hi:"स्थान खोलें",bn:"অবস্থান খুলুন",fr:"Ouvrir l’emplacement",ha:"Buɗe wuri",sw:"Fungua eneo",uz:"Joylashuvni ochish"},
    required:{ar:"أكمل اسم المستلم وصورة التسليم والتوقيع المطلوب.",en:"Complete the receiver name, delivery photo and required signature.",id:"Lengkapi nama penerima, foto pengiriman, dan tanda tangan.",ur:"وصول کنندہ کا نام، تصویر اور مطلوبہ دستخط مکمل کریں۔",hi:"प्राप्तकर्ता का नाम, डिलीवरी फ़ोटो और आवश्यक हस्ताक्षर पूरा करें।",bn:"গ্রহীতার নাম, ডেলিভারি ছবি ও প্রয়োজনীয় স্বাক্ষর দিন।",fr:"Complétez le nom, la photo et la signature requise.",ha:"Cika sunan mai karɓa, hoto da sa hannun da ake buƙata.",sw:"Jaza jina la mpokeaji, picha na sahihi inayohitajika.",uz:"Qabul qiluvchi nomi, rasm va kerakli imzoni kiriting."},
  };
  const tr = (key) => T[key]?.[lang] || T[key]?.en || key;
  const esc = (value) => frappe.utils.escape_html(String(value ?? ""));
  const page = frappe.ui.make_app_page({parent: wrapper, title: tr(isManager ? "field_delivery" : "my_trips"), single_column: true});
  const $root = $(page.body).attr("dir", rtl ? "rtl" : "ltr");
  let trips = [];
  let selectedTrip = null;
  let deliveryImageData = "";
  let signatureTouched = false;

  const statusKey = {
    "مخططة / Planned":"planned", "تم التحميل / Loaded":"loaded", "في الطريق / In Transit":"in_transit",
    "وصلت / Arrived":"arrived", "تم التسليم / Delivered":"delivered", "متأخرة / Delayed":"delayed",
  };
  const statusText = {
    planned:{ar:"مخططة",en:"Planned",id:"Direncanakan",ur:"منصوبہ بند",hi:"नियोजित",bn:"পরিকল্পিত",fr:"Planifié",ha:"An tsara",sw:"Imepangwa",uz:"Rejalashtirilgan"},
    loaded:{ar:"تم التحميل",en:"Loaded",id:"Dimuat",ur:"لوڈ ہو گیا",hi:"लोड हो गया",bn:"লোড হয়েছে",fr:"Chargé",ha:"An loda",sw:"Imepakiwa",uz:"Yuklandi"},
    in_transit:{ar:"في الطريق",en:"In transit",id:"Dalam perjalanan",ur:"راستے میں",hi:"रास्ते में",bn:"পথে",fr:"En route",ha:"A hanya",sw:"Njiani",uz:"Yo‘lda"},
    arrived:{ar:"وصلت",en:"Arrived",id:"Tiba",ur:"پہنچ گیا",hi:"पहुँच गया",bn:"পৌঁছেছে",fr:"Arrivé",ha:"An isa",sw:"Imefika",uz:"Yetib keldi"},
    delivered:{ar:"تم التسليم",en:"Delivered",id:"Terkirim",ur:"ڈیلیور ہو گیا",hi:"डिलीवर हो गया",bn:"ডেলিভারি হয়েছে",fr:"Livré",ha:"An isar",sw:"Imewasilishwa",uz:"Yetkazildi"},
    delayed:{ar:"متأخرة",en:"Delayed",id:"Terlambat",ur:"تاخیر",hi:"विलंबित",bn:"বিলম্বিত",fr:"En retard",ha:"An makara",sw:"Imechelewa",uz:"Kechikdi"},
  };
  const quickNotes = {
    delivered_ok:{ar:"تم التسليم بالكامل دون ملاحظات",en:"Delivered in full without issues",id:"Terkirim penuh tanpa masalah",ur:"بغیر مسئلے مکمل ڈیلیوری",hi:"बिना समस्या पूर्ण डिलीवरी",bn:"সমস্যা ছাড়াই সম্পূর্ণ ডেলিভারি",fr:"Livré entièrement sans incident",ha:"An isar gaba ɗaya ba tare da matsala ba",sw:"Imewasilishwa yote bila tatizo",uz:"Muammosiz to‘liq yetkazildi"},
    receiver_delay:{ar:"تأخر حضور المستلم",en:"Receiver was delayed",id:"Penerima terlambat",ur:"وصول کنندہ تاخیر سے آیا",hi:"प्राप्तकर्ता देर से आया",bn:"গ্রহীতা দেরি করেছেন",fr:"Le destinataire était en retard",ha:"Mai karɓa ya makara",sw:"Mpokeaji alichelewa",uz:"Qabul qiluvchi kechikdi"},
    quantity_issue:{ar:"يوجد اختلاف في الكمية",en:"Quantity discrepancy",id:"Perbedaan jumlah",ur:"مقدار میں فرق",hi:"मात्रा में अंतर",bn:"পরিমাণে পার্থক্য",fr:"Écart de quantité",ha:"Akwai bambancin adadi",sw:"Kuna tofauti ya kiasi",uz:"Miqdorda farq bor"},
    access_issue:{ar:"تعذر الوصول إلى موقع التسليم",en:"Could not access delivery location",id:"Lokasi tidak dapat diakses",ur:"ڈیلیوری مقام تک رسائی نہیں ہوئی",hi:"डिलीवरी स्थान तक पहुँच नहीं मिली",bn:"ডেলিভারি স্থানে প্রবেশ সম্ভব হয়নি",fr:"Accès au site impossible",ha:"Ba a iya shiga wurin isarwa ba",sw:"Haikuwezekana kufika eneo la uwasilishaji",uz:"Yetkazish joyiga kirib bo‘lmadi"},
    receiver_refused:{ar:"رفض المستلم استلام الشحنة",en:"Receiver refused delivery",id:"Penerima menolak kiriman",ur:"وصول کنندہ نے ڈیلیوری مسترد کی",hi:"प्राप्तकर्ता ने डिलीवरी अस्वीकार की",bn:"গ্রহীতা ডেলিভারি প্রত্যাখ্যান করেছেন",fr:"Le destinataire a refusé",ha:"Mai karɓa ya ƙi karɓa",sw:"Mpokeaji amekataa kupokea",uz:"Qabul qiluvchi yetkazmani rad etdi"},
  };

  $root.html(`
    <style>
      .wafd-driver-shell{max-width:760px;margin:12px auto 44px;padding:0 12px;color:#1c1d21}.wafd-driver-nav{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.wafd-driver-nav button{height:42px;border:1px solid #ded6c7;border-radius:12px;background:#f7f4ec;padding:0 14px;font-weight:750;color:#5f4819}.wafd-trip-list{display:grid;gap:13px}.wafd-trip-card{border:1px solid #e5dfd2;border-radius:20px;background:#fff;padding:17px;box-shadow:0 8px 24px rgba(20,21,25,.05)}.wafd-trip-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.wafd-trip-head h3{font-size:19px;margin:0;font-weight:850}.wafd-trip-status{border-radius:999px;background:#f1ead9;color:#765a20;padding:6px 10px;font-size:12px;font-weight:800;white-space:nowrap}.wafd-trip-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:14px 0}.wafd-trip-info{background:#f8f7f3;border-radius:12px;padding:10px}.wafd-trip-info small,.wafd-trip-info b{display:block}.wafd-trip-info small{color:#7a7d82;font-size:11px}.wafd-trip-info b{margin-top:3px}.wafd-loading-evidence{display:flex;gap:10px;align-items:center;margin-top:10px}.wafd-loading-evidence img{width:86px;height:70px;border-radius:11px;object-fit:cover;border:1px solid #e0d9ca}.wafd-trip-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.wafd-trip-actions button,.wafd-proof-submit{border:0;border-radius:12px;background:#1d1e22;color:#fff;padding:11px 15px;font-weight:800}.wafd-trip-actions .secondary{background:#c9972d}.wafd-trip-actions a{border:1px solid #ded6c7;border-radius:12px;padding:10px 14px;color:#6f531a;text-decoration:none;font-weight:750}.wafd-driver-empty{text-align:center;padding:70px 18px;color:#74777d;background:#fff;border:1px solid #e8e2d7;border-radius:20px}.wafd-driver-modal{position:fixed;inset:0;z-index:1200;background:rgba(12,13,16,.56);display:flex;align-items:flex-end;justify-content:center}.wafd-driver-modal[hidden]{display:none}.wafd-proof-panel{width:min(760px,100%);max-height:92vh;overflow:auto;background:#fff;border-radius:24px 24px 0 0;padding:20px 18px calc(24px + env(safe-area-inset-bottom));box-shadow:0 -18px 48px rgba(0,0,0,.18)}.wafd-proof-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}.wafd-proof-head h2{font-size:21px;margin:0}.wafd-proof-head button{border:0;border-radius:10px;background:#f2efe8;padding:8px 12px}.wafd-proof-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.wafd-proof-field.full{grid-column:1/-1}.wafd-proof-field label{display:block;font-weight:750;margin-bottom:6px}.wafd-proof-field input,.wafd-proof-field select,.wafd-proof-field textarea{width:100%;border:1px solid #ddd6c8;border-radius:12px;background:#faf9f6;padding:10px;min-height:44px}.wafd-proof-field textarea{min-height:86px}.wafd-photo-preview{display:none;width:100%;max-height:220px;object-fit:contain;border-radius:12px;background:#f5f4f1;margin-top:9px}.wafd-signature{width:100%;height:160px;border:1px solid #d8d0c1;border-radius:12px;background:#fff;touch-action:none}.wafd-clear-signature{margin-top:7px;border:1px solid #ddd6c8;border-radius:9px;background:#fff;padding:8px 11px}.wafd-proof-submit{width:100%;margin-top:16px}.wafd-proof-done{margin-top:12px;padding:11px;border-radius:12px;background:#e8f4ea;color:#2d6938;font-weight:750}
      @media(max-width:600px){.wafd-trip-grid,.wafd-proof-form{grid-template-columns:1fr}.wafd-proof-field.full{grid-column:auto}.wafd-driver-shell{padding:0 9px}}
    </style>
    <div class="wafd-driver-shell">
      <div class="wafd-driver-nav"><button type="button" id="wafd-driver-back">${esc(tr("back"))}</button><button type="button" id="wafd-driver-refresh">${esc(tr("refresh"))}</button></div>
      <div id="wafd-driver-list"><div class="wafd-driver-empty">${esc(tr("refresh"))}...</div></div>
    </div>
    <div class="wafd-driver-modal" id="wafd-proof-modal" hidden><div class="wafd-proof-panel"><div class="wafd-proof-head"><h2>${esc(tr("proof"))}</h2><button type="button" id="wafd-proof-close">${esc(tr("close"))}</button></div><div id="wafd-proof-content"></div></div></div>
  `);

  function fmtDate(value) {
    return value ? frappe.datetime.str_to_user(value) : "—";
  }
  function tripStatus(value) {
    const key = statusKey[value];
    return key ? (statusText[key]?.[lang] || statusText[key]?.en) : value;
  }
  function hotelName(trip) {
    return lang === "ar" ? (trip.hotel_name_ar || trip.hotel) : (trip.hotel_name_en || trip.hotel_name_ar || trip.hotel);
  }
  function renderTrips() {
    if (!trips.length) {
      $root.find("#wafd-driver-list").html(`<div class="wafd-driver-empty">${esc(tr(isManager ? "no_trips_manager" : "no_trips"))}</div>`);
      return;
    }
    $root.find("#wafd-driver-list").html(`<div class="wafd-trip-list">${trips.map((trip) => {
      const loading = trip.loading || {};
      const proof = trip.proof || null;
      let actions = "";
      if (["مخططة / Planned", "تم التحميل / Loaded"].includes(trip.status)) actions += `<button type="button" data-action="start" data-trip="${esc(trip.name)}">${esc(tr("start"))}</button>`;
      if (["في الطريق / In Transit", "متأخرة / Delayed"].includes(trip.status)) actions += `<button type="button" class="secondary" data-action="arrive" data-trip="${esc(trip.name)}">${esc(tr("mark_arrived"))}</button>`;
      if (trip.status === "وصلت / Arrived" && !proof) actions += `<button type="button" data-action="proof" data-trip="${esc(trip.name)}">${esc(tr("proof"))}</button>`;
      if (proof) actions += `<div class="wafd-proof-done">${esc(tr("delivered"))}: ${esc(proof.receiver_name || "")}</div>`;
      return `<article class="wafd-trip-card"><div class="wafd-trip-head"><h3>${esc(hotelName(trip))}</h3><span class="wafd-trip-status">${esc(tripStatus(trip.status))}</span></div><div class="wafd-trip-grid">${isManager ? `<div class="wafd-trip-info"><small>${esc(tr("driver"))}</small><b>${esc(trip.driver || "—")}</b></div>` : ""}<div class="wafd-trip-info"><small>${esc(tr("vehicle"))}</small><b>${esc(trip.vehicle)}</b></div><div class="wafd-trip-info"><small>${esc(tr("quantity"))}</small><b>${esc(trip.quantity)}</b></div><div class="wafd-trip-info"><small>${esc(tr("arrival"))}</small><b>${esc(fmtDate(trip.planned_arrival))}</b></div><div class="wafd-trip-info"><small>${esc(tr("seal"))}</small><b>${esc(loading.seal_number || "—")}</b></div></div>${loading.loading_photo ? `<div class="wafd-loading-evidence"><img src="${esc(loading.loading_photo)}" alt="${esc(tr("loading_photo"))}"><div><b>${esc(tr("loading_photo"))}</b><small>${esc(tr("uploaded_by"))}: ${esc(loading.loading_photo_uploaded_by || loading.supervisor || "—")}</small></div></div>` : ""}<div class="wafd-trip-actions">${actions}${trip.map_url ? `<a href="${esc(trip.map_url)}" target="_blank" rel="noopener">${esc(tr("open_map"))}</a>` : ""}</div></article>`;
    }).join("")}</div>`);
  }
  async function loadTrips() {
    const response = await frappe.call({method: "wafd_one.driver_portal.list_my_trips", freeze: true});
    trips = response.message?.trips || [];
    renderTrips();
  }
  async function runStatus(tripName, action) {
    await frappe.call({method: "wafd_one.driver_portal.set_my_trip_status", args: {trip_name: tripName, action}, freeze: true});
    await loadTrips();
    if (action === "arrive") openProof(tripName);
  }
  function openProof(tripName) {
    selectedTrip = trips.find((trip) => trip.name === tripName);
    if (!selectedTrip) return;
    deliveryImageData = "";
    signatureTouched = false;
    const options = Object.entries(quickNotes).map(([code, values]) => `<option value="${esc(code)}">${esc(values[lang] || values.en)}</option>`).join("");
    $root.find("#wafd-proof-content").html(`<div class="wafd-proof-form"><div class="wafd-proof-field"><label>${esc(tr("receiver"))}</label><input id="wafd-receiver-name" autocomplete="name"></div><div class="wafd-proof-field"><label>${esc(tr("mobile"))}</label><input id="wafd-receiver-mobile" type="tel" dir="ltr" autocomplete="tel"></div><div class="wafd-proof-field"><label>${esc(tr("received"))}</label><input id="wafd-received-qty" type="number" min="0" value="${esc(selectedTrip.quantity)}"></div><div class="wafd-proof-field"><label>${esc(tr("rejected"))}</label><input id="wafd-rejected-qty" type="number" min="0" value="0"></div><div class="wafd-proof-field full"><label>${esc(tr("acceptance"))}</label><select id="wafd-proof-status"><option value="مقبول بالكامل / Fully Accepted">${esc(tr("full"))}</option><option value="مقبول جزئياً / Partially Accepted">${esc(tr("partial"))}</option><option value="مرفوض / Rejected">${esc(tr("refused"))}</option></select></div><div class="wafd-proof-field full"><label>${esc(tr("quick_note"))}</label><select id="wafd-quick-note"><option value="">${esc(tr("choose"))}</option>${options}</select></div><div class="wafd-proof-field full"><label>${esc(tr("notes"))}</label><textarea id="wafd-proof-notes"></textarea></div><div class="wafd-proof-field full"><label>${esc(tr("photo"))}</label><input id="wafd-delivery-photo" type="file" accept="image/*" capture="environment"><img class="wafd-photo-preview" id="wafd-photo-preview"></div><div class="wafd-proof-field full" id="wafd-signature-field"><label>${esc(tr("signature"))}</label><canvas class="wafd-signature" id="wafd-signature"></canvas><button type="button" class="wafd-clear-signature" id="wafd-clear-signature">${esc(tr("clear"))}</button></div></div><button type="button" class="wafd-proof-submit" id="wafd-proof-submit">${esc(tr("submit"))}</button>`);
    $root.find("#wafd-proof-modal").removeAttr("hidden");
    setupSignature();
  }
  function closeProof() {
    $root.find("#wafd-proof-modal").attr("hidden", true);
    selectedTrip = null;
  }
  function setupSignature() {
    const canvas = $root.find("#wafd-signature")[0];
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.round(rect.width * ratio));
    canvas.height = Math.max(1, Math.round(rect.height * ratio));
    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio); ctx.lineWidth = 2.2; ctx.lineCap = "round"; ctx.strokeStyle = "#17181c";
    let drawing = false;
    const point = (event) => {const r = canvas.getBoundingClientRect(); const touch = event.touches?.[0] || event.changedTouches?.[0] || event; return {x: touch.clientX-r.left, y: touch.clientY-r.top};};
    const start = (event) => {event.preventDefault(); drawing=true; signatureTouched=true; const p=point(event); ctx.beginPath(); ctx.moveTo(p.x,p.y);};
    const move = (event) => {if(!drawing)return; event.preventDefault(); const p=point(event); ctx.lineTo(p.x,p.y); ctx.stroke();};
    const end = (event) => {if(drawing)event.preventDefault(); drawing=false;};
    ["pointerdown","touchstart"].forEach((name)=>canvas.addEventListener(name,start,{passive:false}));
    ["pointermove","touchmove"].forEach((name)=>canvas.addEventListener(name,move,{passive:false}));
    ["pointerup","pointercancel","touchend","touchcancel"].forEach((name)=>canvas.addEventListener(name,end,{passive:false}));
    $root.find("#wafd-clear-signature").on("click",()=>{ctx.clearRect(0,0,canvas.width,canvas.height);signatureTouched=false;});
  }
  function compressDriverImage(file, maxDimension=1600, quality=.82) {
    return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onerror=()=>reject(new Error("image"));reader.onload=()=>{const image=new Image();image.onerror=()=>reject(new Error("image"));image.onload=()=>{const scale=Math.min(1,maxDimension/Math.max(image.naturalWidth,image.naturalHeight));const canvas=document.createElement("canvas");canvas.width=Math.max(1,Math.round(image.naturalWidth*scale));canvas.height=Math.max(1,Math.round(image.naturalHeight*scale));canvas.getContext("2d").drawImage(image,0,0,canvas.width,canvas.height);resolve(canvas.toDataURL("image/jpeg",quality));};image.src=reader.result;};reader.readAsDataURL(file);});
  }
  async function submitProof() {
    if (!selectedTrip) return;
    const proofStatus = $root.find("#wafd-proof-status").val();
    const canvas = $root.find("#wafd-signature")[0];
    const signatureData = signatureTouched ? canvas.toDataURL("image/png") : "";
    const receiverName = String($root.find("#wafd-receiver-name").val() || "").trim();
    if (!receiverName || !deliveryImageData || (proofStatus !== "مرفوض / Rejected" && !signatureData)) {
      frappe.msgprint(tr("required"));
      return;
    }
    const response = await frappe.call({
      method:"wafd_one.driver_portal.submit_delivery_proof",
      args:{trip_name:selectedTrip.name,receiver_name:receiverName,receiver_mobile:$root.find("#wafd-receiver-mobile").val(),received_quantity:$root.find("#wafd-received-qty").val(),rejected_quantity:$root.find("#wafd-rejected-qty").val(),status:proofStatus,operational_note_code:$root.find("#wafd-quick-note").val(),notes:$root.find("#wafd-proof-notes").val(),notes_language:lang,image_data:deliveryImageData,signature_data:signatureData},
      freeze:true,freeze_message:tr("saving"),
    });
    if (response.message?.name) {frappe.show_alert({message:tr("delivered"),indicator:"green"},6);closeProof();await loadTrips();}
  }

  $root.on("click", "#wafd-driver-back", () => frappe.set_route("wafd-role-home"));
  $root.on("click", "#wafd-driver-refresh", loadTrips);
  $root.on("click", "[data-action]", async function(){const action=$(this).attr("data-action");const trip=$(this).attr("data-trip");if(action==="proof")openProof(trip);else await runStatus(trip,action);});
  $root.on("click", "#wafd-proof-close", closeProof);
  $root.on("change", "#wafd-delivery-photo", async function(){const file=this.files?.[0];if(!file)return;deliveryImageData=await compressDriverImage(file);$root.find("#wafd-photo-preview").attr("src",deliveryImageData).show();});
  $root.on("change", "#wafd-proof-status", function(){$root.find("#wafd-signature-field").toggle($(this).val()!=="مرفوض / Rejected");});
  $root.on("click", "#wafd-proof-submit", submitProof);
  wrapper.wafdRefreshTrips = loadTrips;
  loadTrips();
};

frappe.pages["wafd-driver-trips"].on_page_show = function (wrapper) {
  // Frappe caches Page instances. Refresh every time the user returns so a
  // trip created by the manager appears without requiring a manual reload.
  if (typeof wrapper.wafdRefreshTrips === "function") wrapper.wafdRefreshTrips();
};
