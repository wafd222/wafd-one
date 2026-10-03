frappe.pages["wafd-delivery-viewer"].on_page_load = function (wrapper) {
  const lang = localStorage.getItem("wafd_lang") || "ar";
  const rtl = lang === "ar" || lang === "ur";
  const ar = lang === "ar";
  const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
  const T = {
    "القائمة": {en:"Menu",id:"Menu",ur:"مینو",hi:"मेनू",bn:"মেনু",fr:"Menu",ha:"Menu",sw:"Menyu",uz:"Menyu"},
    "اللغة": {en:"Language",id:"Bahasa",ur:"زبان",hi:"भाषा",bn:"ভাষা",fr:"Langue",ha:"Harshe",sw:"Lugha",uz:"Til"},
    "تسجيل الخروج": {en:"Logout",id:"Keluar",ur:"لاگ آؤٹ",hi:"लॉग आउट",bn:"লগআউট",fr:"Déconnexion",ha:"Fita",sw:"Ondoka",uz:"Chiqish"},
    "بيانات التسليم": {en:"Delivery Data",id:"Data Pengiriman",ur:"ڈیلیوری ڈیٹا",hi:"डिलीवरी डेटा",bn:"ডেলিভারি তথ্য",fr:"Données de livraison",ha:"Bayanan Isarwa",sw:"Taarifa za Usafirishaji",uz:"Yetkazib berish ma'lumotlari"},
    "شاشة للقراءة فقط — لا يمكن الإضافة أو التعديل": {en:"Read-only screen — editing is disabled",id:"Layar hanya-baca — penambahan atau pengeditan dinonaktifkan",ur:"صرف پڑھنے کی اسکرین — اضافہ یا ترمیم ممکن نہیں",hi:"केवल-पठन स्क्रीन — जोड़ना या संपादन अक्षम है",bn:"শুধু-পঠন স্ক্রিন — যোগ বা সম্পাদনা নিষ্ক্রিয়",fr:"Écran en lecture seule — ajout et modification désactivés",ha:"Allon karatu kawai — ba a yarda da ƙara ko gyarawa ba",sw:"Skrini ya kusoma-tu — kuongeza au kuhariri kumezimwa",uz:"Faqat o‘qish ekrani — qo‘shish yoki tahrirlash o‘chirilgan"},
    "حالات التسليم": {en:"Delivery statuses",id:"Status pengiriman",ur:"ڈیلیوری کی حالتیں",hi:"डिलीवरी स्थिति",bn:"ডেলিভারি স্ট্যাটাস",fr:"Statuts de livraison",ha:"Matsayin isarwa",sw:"Hali za usafirishaji",uz:"Yetkazib berish holatlari"},
    "في الطريق": {en:"In transit",id:"Dalam perjalanan",ur:"راستے میں",hi:"रास्ते में",bn:"পথে",fr:"En route",ha:"A hanya",sw:"Njiani",uz:"Yo‘lda"},
    "مخططة": {en:"Planned",id:"Direncanakan",ur:"منصوبہ بند",hi:"नियोजित",bn:"পরিকল্পিত",fr:"Planifié",ha:"An shirya",sw:"Imepangwa",uz:"Rejalashtirilgan"},
    "متأخرة أو غير موثقة": {en:"Late or undocumented",id:"Terlambat atau belum didokumentasikan",ur:"تاخیر شدہ یا غیر دستاویزی",hi:"देर से या बिना दस्तावेज़",bn:"দেরিতে বা নথিবিহীন",fr:"En retard ou non documenté",ha:"Jinkiri ko ba a rubuta ba",sw:"Imechelewa au haijaandikwa",uz:"Kechikkan yoki hujjatlashtirilmagan"},
    "تم التسليم": {en:"Delivered",id:"Terkirim",ur:"ڈیلیور شدہ",hi:"डिलीवर किया गया",bn:"ডেলিভার হয়েছে",fr:"Livré",ha:"An isar",sw:"Imewasilishwa",uz:"Yetkazildi"},
    "العميل": {en:"Customer",id:"Pelanggan",ur:"گاہک",hi:"ग्राहक",bn:"গ্রাহক",fr:"Client",ha:"Abokin ciniki",sw:"Mteja",uz:"Mijoz"},
    "الجهة أو الفندق": {en:"Destination",id:"Tujuan",ur:"منزل",hi:"गंतव्य",bn:"গন্তব্য",fr:"Destination",ha:"Wurin zuwa",sw:"Mahali pa kwenda",uz:"Manzil"},
    "نوع الوجبة": {en:"Meal",id:"Jenis makanan",ur:"کھانے کی قسم",hi:"भोजन",bn:"খাবার",fr:"Repas",ha:"Nau'in abinci",sw:"Aina ya chakula",uz:"Taom turi"},
    "اسم السائق": {en:"Driver",id:"Nama pengemudi",ur:"ڈرائیور",hi:"ड्राइवर",bn:"চালক",fr:"Chauffeur",ha:"Direba",sw:"Dereva",uz:"Haydovchi"},
    "رقم الجوال": {en:"Mobile",id:"Nomor ponsel",ur:"موبائل",hi:"मोबाइल",bn:"মোবাইল",fr:"Mobile",ha:"Lambar waya",sw:"Simu",uz:"Telefon"},
    "رقم اللوحة": {en:"Plate number",id:"Nomor plat",ur:"نمبر پلیٹ",hi:"प्लेट नंबर",bn:"প্লেট নম্বর",fr:"Numéro de plaque",ha:"Lambar mota",sw:"Nambari ya gari",uz:"Davlat raqami"},
    "موعد التوصيل": {en:"Scheduled delivery",id:"Jadwal pengiriman",ur:"مقررہ ڈیلیوری",hi:"निर्धारित डिलीवरी",bn:"নির্ধারিত ডেলিভারি",fr:"Livraison prévue",ha:"Lokacin isarwa",sw:"Muda wa usafirishaji",uz:"Rejalashtirilgan yetkazib berish"},
    "عدد الوجبات": {en:"Meals",id:"Jumlah makanan",ur:"کھانوں کی تعداد",hi:"भोजन की संख्या",bn:"খাবারের সংখ্যা",fr:"Repas",ha:"Adadin abinci",sw:"Idadi ya milo",uz:"Taomlar soni"},
    "عدد السفندشات": {en:"Safandash",id:"Safandash",ur:"سفندش",hi:"सफंदश",bn:"সাফান্দাশ",fr:"Safandash",ha:"Safandash",sw:"Safandash",uz:"Safandash"},
    "عدد السخانات Hot Cabinet": {en:"Hot Cabinets",id:"Hot Cabinet",ur:"ہاٹ کیبنٹ",hi:"हॉट कैबिनेट",bn:"হট ক্যাবিনেট",fr:"Armoires chauffantes",ha:"Hot Cabinet",sw:"Hot Cabinet",uz:"Issiq shkaflar"},
    "استلام السائق": {en:"Driver accepted",id:"Pengemudi menerima",ur:"ڈرائیور نے قبول کیا",hi:"ड्राइवर ने स्वीकार किया",bn:"চালক গ্রহণ করেছেন",fr:"Accepté par le chauffeur",ha:"Direba ya karɓa",sw:"Dereva amekubali",uz:"Haydovchi qabul qildi"},
    "وقت الخروج": {en:"Departure",id:"Keberangkatan",ur:"روانگی",hi:"प्रस्थान",bn:"প্রস্থান",fr:"Départ",ha:"Tashi",sw:"Kuondoka",uz:"Jo‘nash"},
    "وقت الوصول": {en:"Arrival",id:"Kedatangan",ur:"آمد",hi:"आगमन",bn:"আগমন",fr:"Arrivée",ha:"Zuwan",sw:"Kuwasili",uz:"Yetib kelish"},
    "التسليم": {en:"Delivered",id:"Terkirim",ur:"ڈیلیور شدہ",hi:"डिलीवर किया गया",bn:"ডেলিভার হয়েছে",fr:"Livré",ha:"An isar",sw:"Imewasilishwa",uz:"Yetkazildi"},
    "اسم المستلم": {en:"Receiver",id:"Nama penerima",ur:"وصول کنندہ",hi:"प्राप्तकर्ता",bn:"গ্রহীতা",fr:"Destinataire",ha:"Sunan mai karɓa",sw:"Mpokeaji",uz:"Qabul qiluvchi"},
    "بانتظار التسليم": {en:"Pending delivery",id:"Menunggu pengiriman",ur:"ڈیلیوری زیر التوا",hi:"डिलीवरी लंबित",bn:"ডেলিভারি অপেক্ষমাণ",fr:"Livraison en attente",ha:"Ana jiran isarwa",sw:"Inasubiri usafirishaji",uz:"Yetkazib berish kutilmoqda"},
    "صورة التسليم": {en:"Delivery photo",id:"Foto pengiriman",ur:"ڈیلیوری کی تصویر",hi:"डिलीवरी फोटो",bn:"ডেলিভারি ছবি",fr:"Photo de livraison",ha:"Hoton isarwa",sw:"Picha ya usafirishaji",uz:"Yetkazib berish rasmi"},
    "لم ترفق صورة التسليم بعد": {en:"Delivery photo is not available yet",id:"Foto pengiriman belum tersedia",ur:"ڈیلیوری کی تصویر ابھی دستیاب نہیں",hi:"डिलीवरी फोटो अभी उपलब्ध नहीं है",bn:"ডেলিভারি ছবি এখনও পাওয়া যায়নি",fr:"La photo de livraison n’est pas encore disponible",ha:"Ba a samu hoton isarwa ba tukuna",sw:"Picha ya usafirishaji bado haipatikani",uz:"Yetkazib berish rasmi hali mavjud emas"},
    "بانتظار التنفيذ": {en:"Pending",id:"Menunggu",ur:"زیر التوا",hi:"लंबित",bn:"অপেক্ষমাণ",fr:"En attente",ha:"Ana jira",sw:"Inasubiri",uz:"Kutilmoqda"},
    "جارٍ تحميل بيانات التسليم…": {en:"Loading delivery data…",id:"Memuat data pengiriman…",ur:"ڈیلیوری ڈیٹا لوڈ ہو رہا ہے…",hi:"डिलीवरी डेटा लोड हो रहा है…",bn:"ডেলিভারি তথ্য লোড হচ্ছে…",fr:"Chargement des données de livraison…",ha:"Ana loda bayanan isarwa…",sw:"Inapakia taarifa za usafirishaji…",uz:"Yetkazib berish ma'lumotlari yuklanmoqda…"},
    "لا توجد عمليات في هذه الحالة حاليًا.": {en:"No deliveries are currently in this status.",id:"Saat ini tidak ada pengiriman dalam status ini.",ur:"اس حالت میں فی الحال کوئی ڈیلیوری نہیں ہے۔",hi:"इस स्थिति में अभी कोई डिलीवरी नहीं है।",bn:"এই অবস্থায় বর্তমানে কোনো ডেলিভারি নেই।",fr:"Aucune livraison n’est actuellement dans ce statut.",ha:"Babu isarwa a wannan matsayi a yanzu.",sw:"Kwa sasa hakuna usafirishaji katika hali hii.",uz:"Hozir bu holatda yetkazib berishlar yo‘q."}
  };
  const tr = (a, e) => lang === "ar" ? a : (T[a]?.[lang] || e || a);
  const languages = {ar:"العربية",en:"English",id:"Bahasa Indonesia",ur:"اردو",hi:"हिन्दी",bn:"বাংলা",fr:"Français",ha:"Hausa",sw:"Kiswahili",uz:"O‘zbekcha"};
  const local = (v) => {
    const raw = String(v || "").trim();
    const parts = raw.split("/").map((x) => x.trim());
    const key = parts[0];
    const valueMap = {
      "في الطريق": "في الطريق", "مخططة": "مخططة", "متأخرة": "متأخرة", "وصلت": "وصلت", "تم التسليم": "تم التسليم",
      "إفطار": "إفطار", "فطور": "فطور", "غداء": "غداء", "عشاء": "عشاء", "وجبة إفطار": "وجبة إفطار", "وجبة غداء": "وجبة غداء", "وجبة عشاء": "وجبة عشاء"
    };
    const mealT = {
      "إفطار": {en:"Breakfast",id:"Sarapan",ur:"ناشتہ",hi:"नाश्ता",bn:"নাশতা",fr:"Petit-déjeuner",ha:"Karin kumallo",sw:"Kifungua kinywa",uz:"Nonushta"},
      "فطور": {en:"Breakfast",id:"Sarapan",ur:"ناشتہ",hi:"नाश्ता",bn:"নাশতা",fr:"Petit-déjeuner",ha:"Karin kumallo",sw:"Kifungua kinywa",uz:"Nonushta"},
      "غداء": {en:"Lunch",id:"Makan siang",ur:"دوپہر کا کھانا",hi:"दोपहर का भोजन",bn:"দুপুরের খাবার",fr:"Déjeuner",ha:"Abincin rana",sw:"Chakula cha mchana",uz:"Tushlik"},
      "عشاء": {en:"Dinner",id:"Makan malam",ur:"رات کا کھانا",hi:"रात का भोजन",bn:"রাতের খাবার",fr:"Dîner",ha:"Abincin dare",sw:"Chakula cha jioni",uz:"Kechki ovqat"}
    };
    if (ar) return valueMap[key] || parts[0] || "—";
    if (mealT[key]?.[lang]) return mealT[key][lang];
    const statusT = {
      "في الطريق": {en:"In transit",id:"Dalam perjalanan",ur:"راستے میں",hi:"रास्ते में",bn:"পথে",fr:"En route",ha:"A hanya",sw:"Njiani",uz:"Yo‘lda"},
      "مخططة": {en:"Planned",id:"Direncanakan",ur:"منصوبہ بند",hi:"नियोजित",bn:"পরিকল্পিত",fr:"Planifié",ha:"An shirya",sw:"Imepangwa",uz:"Rejalashtirilgan"},
      "متأخرة": {en:"Delayed",id:"Terlambat",ur:"تاخیر شدہ",hi:"विलंबित",bn:"বিলম্বিত",fr:"Retardé",ha:"An jinkirta",sw:"Imechelewa",uz:"Kechikkan"},
      "وصلت": {en:"Arrived",id:"Tiba",ur:"پہنچ گیا",hi:"पहुंचा",bn:"পৌঁছেছে",fr:"Arrivé",ha:"Ya isa",sw:"Imefika",uz:"Yetib keldi"},
      "تم التسليم": {en:"Delivered",id:"Terkirim",ur:"ڈیلیور شدہ",hi:"डिलीवर किया गया",bn:"ডেলিভার হয়েছে",fr:"Livré",ha:"An isar",sw:"Imewasilishwa",uz:"Yetkazildi"}
    };
    return statusT[key]?.[lang] || parts[parts.length - 1] || raw || "—";
  };
  const fmt = (v) => v ? (frappe.datetime.str_to_user(v) || v) : tr("بانتظار التنفيذ", "Pending");
  const page = frappe.ui.make_app_page({parent: wrapper, title: tr("بيانات التسليم", "Delivery Data"), single_column: true});
  const $root = $(page.body).attr("dir", rtl ? "rtl" : "ltr");
  let data = {};
  let view = "in_transit";
  const queues = [
    {key:"in_transit", label:tr("في الطريق", "In transit")},
    {key:"planned", label:tr("مخططة", "Planned")},
    {key:"attention", label:tr("متأخرة أو غير موثقة", "Late or undocumented")},
    {key:"delivered", label:tr("تم التسليم", "Delivered")},
  ];

  function bindViewerMenu() {
    const $menu = $root.find(".wafd-pwa-menu");
    const $button = $root.find(".wafd-pwa-menu-btn");
    const close = () => {$menu.attr("hidden", true); $button.attr("aria-expanded", "false");};
    $button.on("click", function (event) {
      event.stopPropagation();
      const open = $menu.attr("hidden") !== undefined;
      if (open) {$menu.removeAttr("hidden"); $button.attr("aria-expanded", "true");} else close();
    });
    $root.find("#wafv-language").on("change", async function () {
      localStorage.setItem("wafd_lang", this.value);
      await frappe.call({method:"wafd_one.language.set_user_language", args:{language:this.value}, freeze:true});
      window.location.reload();
    });
    $root.find("[data-wafv-logout]").on("click", function () {
      close();
      if (frappe.app?.logout) frappe.app.logout();
      else window.location.assign("/?cmd=web_logout");
    });
    $(document).off("click.wafdViewerMenu").on("click.wafdViewerMenu", function (event) {
      if (!$(event.target).closest(".wafd-pwa-appbar").length) close();
    });
  }

  function optionalCount(label, value, equipment=false) {
    return Number(value) > 0
      ? `<div class="${equipment ? "is-equipment" : ""}"><small>${esc(label)}</small><b>${esc(value)}</b></div>`
      : "";
  }

  function renderTrip(row) {
    const photo = row.has_delivery_photo
      ? `<img class="wafv-photo" loading="lazy" src="/api/method/wafd_one.delivery_tracking.get_my_delivery_photo?assignment_name=${encodeURIComponent(row.assignment_name)}" alt="${esc(tr("صورة التسليم", "Delivery photo"))}">`
      : `<div class="wafv-photo-empty">${esc(tr("لم ترفق صورة التسليم بعد", "Delivery photo is not available yet"))}</div>`;
    const counts = [
      optionalCount(tr("عدد الوجبات", "Meals"), row.quantity),
      optionalCount(tr("عدد السفندشات", "Safandash"), row.safandash_count, true),
      optionalCount(tr("عدد السخانات Hot Cabinet", "Hot Cabinets"), row.hot_cabinet_count, true),
    ].join("");
    return `<article class="wafv-card is-${esc(row.board_bucket || "planned")}">
      ${row.schedule_customer ? `<div class="wafv-customer"><small>${esc(tr("العميل", "Customer"))}</small><b>${esc(row.schedule_customer)}</b></div>` : ""}
      <div class="wafv-card-head"><div><small>${esc(tr("الجهة أو الفندق", "Destination"))}</small><h2>${esc(ar ? row.destination_name : (row.destination_name_en || row.destination_name))}</h2></div><span>${esc(local(row.status))}</span></div>
      <div class="wafv-grid">
        <div><small>${esc(tr("نوع الوجبة", "Meal"))}</small><b>${esc(local(row.meal_type))}</b></div>
        <div><small>${esc(tr("اسم السائق", "Driver"))}</small><b>${esc(row.driver_name || "—")}</b></div>
        <div><small>${esc(tr("رقم الجوال", "Mobile"))}</small><b dir="ltr">${esc(row.driver_mobile || "—")}</b></div>
        <div><small>${esc(tr("رقم اللوحة", "Plate number"))}</small><b>${esc(row.plate_number || "—")}</b></div>
        <div><small>${esc(tr("موعد التوصيل", "Scheduled delivery"))}</small><b>${esc(fmt(row.planned_arrival || row.trip_date))}</b></div>
        ${counts}
      </div>
      <div class="wafv-timeline">
        ${[[tr("استلام السائق", "Driver accepted"), row.driver_accepted_on], [tr("وقت الخروج", "Departure"), row.departure_time], [tr("وقت الوصول", "Arrival"), row.arrival_time], [tr("التسليم", "Delivered"), row.delivery_time]].map(([label, value]) => `<div class="${value ? "done" : ""}"><i>${value ? "✓" : "•"}</i><span><b>${esc(label)}</b><small>${esc(fmt(value))}</small></span></div>`).join("")}
      </div>
      <div class="wafv-proof"><div><small>${esc(tr("اسم المستلم", "Receiver"))}</small><b>${esc(row.receiver_name || tr("بانتظار التسليم", "Pending delivery"))}</b></div>${photo}</div>
    </article>`;
  }

  function renderPage() {
    const rows = (data.trips || []).filter((row) => row.board_bucket === view);
    const tabs = queues.map((queue) => `<button type="button" data-wafv-view="${queue.key}" class="${view === queue.key ? "is-active" : ""}"><span>${esc(queue.label)}</span><b>${esc(data.summary?.[queue.key] || 0)}</b></button>`).join("");
    $root.html(`<style>
      .wafv-shell{max-width:900px;margin:16px auto 45px;padding:0 11px;color:#1d1e22}.wafv-hero{background:linear-gradient(135deg,#18191d,#28272b 67%,#59451f);color:#fff;border-radius:25px;padding:22px;margin-bottom:15px}.wafv-hero small{color:#e1c46e;font-weight:800}.wafv-hero h1{margin:5px 0;font-size:27px}.wafv-hero p{margin:0;color:#d3d3d5}.wafv-tabs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:15px 0}.wafv-tabs button{display:flex;align-items:center;justify-content:center;gap:7px;min-width:0;min-height:48px;border:1px solid #dfd7c7;background:#fff;border-radius:14px;padding:10px 8px;color:#176be6;font-weight:800}.wafv-tabs button span{overflow-wrap:anywhere}.wafv-tabs button b{display:grid;place-items:center;min-width:25px;height:25px;padding:0 6px;border-radius:999px;background:#f2ead8;color:#765716}.wafv-tabs button.is-active{background:#1d1e22;color:#fff}.wafv-tabs button.is-active b{background:#cf9a29;color:#fff}.wafv-card{background:#fff;border:1px solid #e8e0d1;border-inline-start:5px solid #d7c8a7;border-radius:22px;padding:18px;margin-bottom:14px;box-shadow:0 8px 24px rgba(22,23,27,.04)}.wafv-card.is-in_transit{border-inline-start-color:#3686c5}.wafv-card.is-attention{border-inline-start-color:#c58728}.wafv-card.is-delivered{border-inline-start-color:#2b8b52}.wafv-customer{display:flex;justify-content:space-between;align-items:center;gap:10px;background:#f8f2e4;border-radius:11px;padding:8px 11px;margin-bottom:12px;color:#765817}.wafv-customer small{color:#8b7b58}.wafv-card-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.wafv-card-head small,.wafv-grid small,.wafv-proof small{display:block;color:#777b82;margin-bottom:4px}.wafv-card-head h2{font-size:22px;margin:0}.wafv-card-head>span{background:#f1e8d5;color:#765817;border-radius:999px;padding:7px 11px;font-size:12px;font-weight:800}.wafv-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:16px}.wafv-grid>div,.wafv-proof>div:first-child{background:#faf9f6;border:1px solid #eee9df;border-radius:13px;padding:11px;min-width:0}.wafv-grid .is-equipment{background:#f7f0e1;border-color:#e6d6b4}.wafv-timeline{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:16px 0}.wafv-timeline>div{display:flex;gap:7px;align-items:center}.wafv-timeline i{width:27px;height:27px;border-radius:50%;background:#ece9e1;display:grid;place-items:center;font-style:normal}.wafv-timeline .done i{background:#28784b;color:#fff}.wafv-timeline b,.wafv-timeline small{display:block}.wafv-timeline small{color:#777b82;font-size:11px}.wafv-proof{display:grid;grid-template-columns:1fr 190px;gap:10px;align-items:stretch;border-top:1px solid #eee8dc;padding-top:14px}.wafv-photo{width:190px;height:125px;object-fit:cover;border-radius:13px;background:#eee}.wafv-photo-empty{display:grid;place-items:center;text-align:center;min-height:100px;border:1px dashed #d8d1c3;border-radius:13px;color:#87898e}.wafv-empty,.wafv-loading{text-align:center;padding:55px 16px;color:#777b82}
      @media(max-width:700px){.wafv-shell{padding:0 8px}.wafv-hero{margin:0 -8px 12px;border-radius:0 0 23px 23px}.wafv-tabs,.wafv-grid,.wafv-timeline{grid-template-columns:1fr 1fr}.wafv-tabs button{min-height:58px}.wafv-proof{grid-template-columns:1fr}.wafv-photo{width:100%;height:210px}}
    </style><section class="wafd-pwa-appbar" aria-label="WAFD ONE"><button type="button" class="wafd-pwa-menu-btn" aria-label="${esc(tr("القائمة", "Menu"))}" aria-expanded="false"><span></span><span></span><span></span></button><strong>WAFD ONE</strong><div class="wafd-pwa-menu" role="menu" hidden><label class="wafd-pwa-language-row" for="wafv-language"><span>文 ${esc(tr("اللغة", "Language"))}</span><select id="wafv-language">${Object.entries(languages).map(([code,name])=>`<option value="${code}" ${code===lang?"selected":""}>${esc(name)}</option>`).join("")}</select></label><button type="button" class="is-danger" data-wafv-logout>↪ <span>${esc(tr("تسجيل الخروج", "Logout"))}</span></button></div></section><main class="wafv-shell"><section class="wafv-hero"><small>WAFD ONE</small><h1>${esc(tr("بيانات التسليم", "Delivery Data"))}</h1><p>${esc(data.viewer_name || "")}</p><p>${esc(tr("شاشة للقراءة فقط — لا يمكن الإضافة أو التعديل", "Read-only screen — editing is disabled"))}</p></section><nav class="wafv-tabs" aria-label="${esc(tr("حالات التسليم", "Delivery statuses"))}">${tabs}</nav><section>${rows.length ? rows.map(renderTrip).join("") : `<div class="wafv-card wafv-empty">${esc(tr("لا توجد عمليات في هذه الحالة حاليًا.", "No deliveries are currently in this status."))}</div>`}</section></main>`);
    bindViewerMenu();
    $root.find("[data-wafv-view]").on("click", function () {
      view = $(this).data("wafv-view");
      renderPage();
    });
  }

  async function load() {
    $root.html(`<div class="wafv-loading">${esc(tr("جارٍ تحميل بيانات التسليم…", "Loading delivery data…"))}</div>`);
    const response = await frappe.call({method: "wafd_one.delivery_tracking.get_my_delivery_tracking"});
    data = response.message || {};
    if (!(data.trips || []).some((row) => row.board_bucket === view)) {
      view = queues.find((queue) => Number(data.summary?.[queue.key]) > 0)?.key || view;
    }
    renderPage();
  }

  wrapper.wafdDeliveryViewerLoad = load;
  load();
};

frappe.pages["wafd-delivery-viewer"].on_page_show = function (wrapper) {
  wrapper.wafdDeliveryViewerLoad?.();
};
