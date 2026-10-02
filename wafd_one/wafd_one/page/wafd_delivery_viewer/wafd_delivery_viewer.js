frappe.pages["wafd-delivery-viewer"].on_page_load = function (wrapper) {
  const lang = localStorage.getItem("wafd_lang") || "ar";
  const ar = lang === "ar";
  const rtl = ["ar", "ur"].includes(lang);
  const translations = {
    id:{"Delivery Data":"Data Pengiriman","Pending":"Menunggu","In transit":"Dalam perjalanan","Planned":"Direncanakan","Late or undocumented":"Terlambat atau belum didokumentasikan","Delivered":"Terkirim","Delivery photo":"Foto pengiriman","Delivery photo is not available yet":"Foto pengiriman belum tersedia","Meals":"Jumlah makanan","Safandash":"Jumlah safandash","Hot Cabinets":"Kabinet pemanas","Customer":"Pelanggan","Destination":"Tujuan","Meal":"Jenis makanan","Driver":"Nama pengemudi","Mobile":"Nomor ponsel","Plate number":"Nomor pelat","Scheduled delivery":"Jadwal pengiriman","Driver accepted":"Diterima pengemudi","Departure":"Waktu berangkat","Arrival":"Waktu tiba","Receiver":"Nama penerima","Pending delivery":"Menunggu penyerahan","Menu":"Menu","Language":"Bahasa","Logout":"Keluar","Read-only screen — editing is disabled":"Layar hanya-baca — tidak dapat ditambah atau diubah","Delivery statuses":"Status pengiriman","No deliveries are currently in this status.":"Tidak ada pengiriman dalam status ini saat ini.","Loading delivery data…":"Memuat data pengiriman…","Loaded":"Dimuat","Arrived":"Tiba","Delayed":"Terlambat","Breakfast":"Sarapan","Lunch":"Makan siang","Dinner":"Makan malam","Iftar":"Iftar","Iftar Saim":"Iftar Saim"},
    ur:{"Delivery Data":"ڈیلیوری ڈیٹا","Pending":"زیر التوا","In transit":"راستے میں","Planned":"منصوبہ بند","Late or undocumented":"تاخیر یا غیر دستاویزی","Delivered":"ڈیلیور ہو گیا","Delivery photo":"ڈیلیوری کی تصویر","Delivery photo is not available yet":"ڈیلیوری کی تصویر ابھی دستیاب نہیں","Meals":"کھانوں کی تعداد","Safandash":"سفندش کی تعداد","Hot Cabinets":"گرم کیبنٹس","Customer":"گاہک","Destination":"منزل","Meal":"کھانے کی قسم","Driver":"ڈرائیور کا نام","Mobile":"موبائل نمبر","Plate number":"پلیٹ نمبر","Scheduled delivery":"مقررہ ڈیلیوری","Driver accepted":"ڈرائیور نے قبول کیا","Departure":"روانگی کا وقت","Arrival":"پہنچنے کا وقت","Receiver":"وصول کنندہ کا نام","Pending delivery":"ڈیلیوری کا انتظار","Menu":"مینو","Language":"زبان","Logout":"لاگ آؤٹ","Read-only screen — editing is disabled":"صرف دیکھنے کی اسکرین — ترمیم ممکن نہیں","Delivery statuses":"ڈیلیوری کی حالتیں","No deliveries are currently in this status.":"اس حالت میں فی الحال کوئی ڈیلیوری نہیں۔","Loading delivery data…":"ڈیلیوری ڈیٹا لوڈ ہو رہا ہے…","Loaded":"لوڈ ہو گیا","Arrived":"پہنچ گیا","Delayed":"تاخیر","Breakfast":"ناشتہ","Lunch":"دوپہر کا کھانا","Dinner":"رات کا کھانا","Iftar":"افطار","Iftar Saim":"افطار صائم"},
    hi:{"Delivery Data":"डिलीवरी डेटा","Pending":"लंबित","In transit":"रास्ते में","Planned":"नियोजित","Late or undocumented":"देर से या बिना दस्तावेज़","Delivered":"वितरित","Delivery photo":"डिलीवरी फोटो","Delivery photo is not available yet":"डिलीवरी फोटो अभी उपलब्ध नहीं है","Meals":"भोजन की संख्या","Safandash":"सफ़ंदाश की संख्या","Hot Cabinets":"हॉट कैबिनेट","Customer":"ग्राहक","Destination":"गंतव्य","Meal":"भोजन का प्रकार","Driver":"ड्राइवर का नाम","Mobile":"मोबाइल नंबर","Plate number":"प्लेट नंबर","Scheduled delivery":"निर्धारित डिलीवरी","Driver accepted":"ड्राइवर ने स्वीकार किया","Departure":"प्रस्थान समय","Arrival":"पहुंचने का समय","Receiver":"प्राप्तकर्ता का नाम","Pending delivery":"डिलीवरी लंबित","Menu":"मेनू","Language":"भाषा","Logout":"लॉग आउट","Read-only screen — editing is disabled":"केवल देखने की स्क्रीन — संपादन बंद है","Delivery statuses":"डिलीवरी स्थितियाँ","No deliveries are currently in this status.":"इस स्थिति में अभी कोई डिलीवरी नहीं है।","Loading delivery data…":"डिलीवरी डेटा लोड हो रहा है…","Loaded":"लोड किया गया","Arrived":"पहुंच गया","Delayed":"विलंबित","Breakfast":"नाश्ता","Lunch":"दोपहर का भोजन","Dinner":"रात का भोजन","Iftar":"इफ्तार","Iftar Saim":"इफ्तार साइम"},
    bn:{"Delivery Data":"ডেলিভারি তথ্য","Pending":"অপেক্ষমাণ","In transit":"পথে আছে","Planned":"পরিকল্পিত","Late or undocumented":"বিলম্বিত বা নথিবিহীন","Delivered":"বিতরণ সম্পন্ন","Delivery photo":"ডেলিভারির ছবি","Delivery photo is not available yet":"ডেলিভারির ছবি এখনও পাওয়া যায়নি","Meals":"খাবারের সংখ্যা","Safandash":"সাফানদাশ সংখ্যা","Hot Cabinets":"হট ক্যাবিনেট","Customer":"গ্রাহক","Destination":"গন্তব্য","Meal":"খাবারের ধরন","Driver":"চালকের নাম","Mobile":"মোবাইল নম্বর","Plate number":"প্লেট নম্বর","Scheduled delivery":"নির্ধারিত ডেলিভারি","Driver accepted":"চালক গ্রহণ করেছেন","Departure":"রওনা হওয়ার সময়","Arrival":"পৌঁছানোর সময়","Receiver":"গ্রহীতার নাম","Pending delivery":"ডেলিভারি অপেক্ষমাণ","Menu":"মেনু","Language":"ভাষা","Logout":"লগ আউট","Read-only screen — editing is disabled":"শুধু দেখার স্ক্রিন — সম্পাদনা বন্ধ","Delivery statuses":"ডেলিভারির অবস্থা","No deliveries are currently in this status.":"এই অবস্থায় বর্তমানে কোনো ডেলিভারি নেই।","Loading delivery data…":"ডেলিভারি তথ্য লোড হচ্ছে…","Loaded":"লোড হয়েছে","Arrived":"পৌঁছেছে","Delayed":"বিলম্বিত","Breakfast":"সকালের নাশতা","Lunch":"দুপুরের খাবার","Dinner":"রাতের খাবার","Iftar":"ইফতার","Iftar Saim":"ইফতার সায়েম"},
    fr:{"Delivery Data":"Données de livraison","Pending":"En attente","In transit":"En route","Planned":"Planifié","Late or undocumented":"En retard ou non documenté","Delivered":"Livré","Delivery photo":"Photo de livraison","Delivery photo is not available yet":"La photo de livraison n’est pas encore disponible","Meals":"Nombre de repas","Safandash":"Nombre de safandash","Hot Cabinets":"Armoires chauffantes","Customer":"Client","Destination":"Destination","Meal":"Type de repas","Driver":"Nom du chauffeur","Mobile":"Téléphone","Plate number":"Immatriculation","Scheduled delivery":"Livraison prévue","Driver accepted":"Accepté par le chauffeur","Departure":"Heure de départ","Arrival":"Heure d’arrivée","Receiver":"Nom du destinataire","Pending delivery":"Livraison en attente","Menu":"Menu","Language":"Langue","Logout":"Déconnexion","Read-only screen — editing is disabled":"Écran en lecture seule — modification désactivée","Delivery statuses":"États des livraisons","No deliveries are currently in this status.":"Aucune livraison dans cet état actuellement.","Loading delivery data…":"Chargement des livraisons…","Loaded":"Chargé","Arrived":"Arrivé","Delayed":"En retard","Breakfast":"Petit-déjeuner","Lunch":"Déjeuner","Dinner":"Dîner","Iftar":"Iftar","Iftar Saim":"Iftar Saim"},
    ha:{"Delivery Data":"Bayanan Isarwa","Pending":"Ana jira","In transit":"A hanya","Planned":"An tsara","Late or undocumented":"Ya makara ko ba a rubuta ba","Delivered":"An isar","Delivery photo":"Hoton isarwa","Delivery photo is not available yet":"Har yanzu babu hoton isarwa","Meals":"Yawan abinci","Safandash":"Yawan safandash","Hot Cabinets":"Akwatunan zafi","Customer":"Abokin ciniki","Destination":"Wurin zuwa","Meal":"Nau'in abinci","Driver":"Sunan direba","Mobile":"Lambar waya","Plate number":"Lambar mota","Scheduled delivery":"Lokacin isarwa","Driver accepted":"Direba ya karɓa","Departure":"Lokacin tashi","Arrival":"Lokacin isa","Receiver":"Sunan mai karɓa","Pending delivery":"Ana jiran isarwa","Menu":"Jeri","Language":"Harshe","Logout":"Fita","Read-only screen — editing is disabled":"Allon kallo kawai — ba a yarda gyara ba","Delivery statuses":"Matsayin isarwa","No deliveries are currently in this status.":"Babu isarwa a wannan matsayi yanzu.","Loading delivery data…":"Ana loda bayanan isarwa…","Loaded":"An loda","Arrived":"An isa","Delayed":"Ya makara","Breakfast":"Karin kumallo","Lunch":"Abincin rana","Dinner":"Abincin dare","Iftar":"Iftar","Iftar Saim":"Iftar Saim"},
    sw:{"Delivery Data":"Taarifa za Usafirishaji","Pending":"Inasubiri","In transit":"Njiani","Planned":"Imepangwa","Late or undocumented":"Imechelewa au haijathibitishwa","Delivered":"Imewasilishwa","Delivery photo":"Picha ya uwasilishaji","Delivery photo is not available yet":"Picha ya uwasilishaji bado haipatikani","Meals":"Idadi ya milo","Safandash":"Idadi ya safandash","Hot Cabinets":"Kabati za joto","Customer":"Mteja","Destination":"Eneo la kufikishia","Meal":"Aina ya mlo","Driver":"Jina la dereva","Mobile":"Namba ya simu","Plate number":"Namba ya gari","Scheduled delivery":"Muda uliopangwa","Driver accepted":"Dereva amekubali","Departure":"Muda wa kuondoka","Arrival":"Muda wa kufika","Receiver":"Jina la mpokeaji","Pending delivery":"Inasubiri kukabidhiwa","Menu":"Menyu","Language":"Lugha","Logout":"Ondoka","Read-only screen — editing is disabled":"Skrini ya kusoma pekee — uhariri umezimwa","Delivery statuses":"Hali za usafirishaji","No deliveries are currently in this status.":"Hakuna usafirishaji katika hali hii kwa sasa.","Loading delivery data…":"Inapakia taarifa za usafirishaji…","Loaded":"Imepakiwa","Arrived":"Imefika","Delayed":"Imechelewa","Breakfast":"Kifungua kinywa","Lunch":"Chakula cha mchana","Dinner":"Chakula cha jioni","Iftar":"Iftar","Iftar Saim":"Iftar Saim"},
    uz:{"Delivery Data":"Yetkazib berish ma’lumotlari","Pending":"Kutilmoqda","In transit":"Yo‘lda","Planned":"Rejalashtirilgan","Late or undocumented":"Kechikkan yoki hujjatsiz","Delivered":"Yetkazildi","Delivery photo":"Yetkazib berish rasmi","Delivery photo is not available yet":"Yetkazib berish rasmi hali mavjud emas","Meals":"Taomlar soni","Safandash":"Safandash soni","Hot Cabinets":"Issiq shkaflar","Customer":"Mijoz","Destination":"Manzil","Meal":"Taom turi","Driver":"Haydovchi ismi","Mobile":"Telefon raqami","Plate number":"Davlat raqami","Scheduled delivery":"Rejalashtirilgan yetkazish","Driver accepted":"Haydovchi qabul qildi","Departure":"Jo‘nash vaqti","Arrival":"Yetib kelish vaqti","Receiver":"Qabul qiluvchi","Pending delivery":"Yetkazish kutilmoqda","Menu":"Menyu","Language":"Til","Logout":"Chiqish","Read-only screen — editing is disabled":"Faqat ko‘rish — tahrirlash o‘chirilgan","Delivery statuses":"Yetkazish holatlari","No deliveries are currently in this status.":"Bu holatda hozir yetkazmalar yo‘q.","Loading delivery data…":"Yetkazish ma’lumotlari yuklanmoqda…","Loaded":"Yuklandi","Arrived":"Yetib keldi","Delayed":"Kechikdi","Breakfast":"Nonushta","Lunch":"Tushlik","Dinner":"Kechki ovqat","Iftar":"Iftar","Iftar Saim":"Iftar Saim"}
  };
  const tr = (a, e) => ar ? a : (translations[lang]?.[e] || e);
  const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
  const languages = {ar:"العربية",en:"English",id:"Bahasa Indonesia",ur:"اردو",hi:"हिन्दी",bn:"বাংলা",fr:"Français",ha:"Hausa",sw:"Kiswahili",uz:"O‘zbekcha"};
  const local = (v) => {
    const parts = String(v || "").split("/").map((x) => x.trim());
    const english = parts[parts.length - 1] === "In Transit" ? "In transit" : parts[parts.length - 1];
    return parts.length > 1 ? tr(parts[0], english) : (translations[lang]?.[String(v || "")] || String(v || "—"));
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
