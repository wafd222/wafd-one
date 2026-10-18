frappe.pages["wafd-cleaning-home"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({ parent: wrapper, title: __("مواد النظافة"), single_column: true });
  const $root = $(page.body).addClass("wafd-cleaning-home");
  const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
  const dictionaries = {
    ar:{dir:"rtl",title:"مواد النظافة",pending:"بانتظار استلامك",custody:"المواد الموجودة لديك",recent:"آخر عمليات الصرف",accept:"تأكيد الاستلام",reject:"رفض",use:"تسجيل صرف",none:"لا توجد بيانات",no_pending:"لم تصل مواد مرحلة من أمين المستودع حتى الآن",refresh:"تحديث",purpose:"غرض الصرف",location:"الموقع",qty:"الكمية",notes:"ملاحظات",save:"حفظ الصرف",reason:"سبب الرفض",received:"المستلم",remaining:"المتبقي"},
    en:{dir:"ltr",title:"Cleaning Materials",pending:"Waiting for receipt",custody:"Materials in your custody",recent:"Recent usage",accept:"Accept receipt",reject:"Reject",use:"Record usage",none:"No records",no_pending:"No posted materials have arrived from the Storekeeper",refresh:"Refresh",purpose:"Purpose",location:"Location",qty:"Quantity",notes:"Notes",save:"Save usage",reason:"Rejection reason",received:"Received",remaining:"Remaining"},
    bn:{dir:"ltr",title:"পরিচ্ছন্নতার সামগ্রী",pending:"গ্রহণের অপেক্ষায়",custody:"আপনার কাছে থাকা সামগ্রী",recent:"সাম্প্রতিক ব্যবহার",accept:"গ্রহণ নিশ্চিত করুন",reject:"প্রত্যাখ্যান",use:"ব্যবহার লিখুন",none:"কোন তথ্য নেই",no_pending:"স্টোরকিপার থেকে এখনো কোনো চূড়ান্ত সামগ্রী আসেনি",refresh:"রিফ্রেশ",purpose:"ব্যবহারের উদ্দেশ্য",location:"স্থান",qty:"পরিমাণ",notes:"নোট",save:"সংরক্ষণ",reason:"প্রত্যাখ্যানের কারণ",received:"প্রাপ্ত",remaining:"অবশিষ্ট"},
    ur:{dir:"rtl",title:"صفائی کا سامان",pending:"وصولی کے منتظر",custody:"آپ کے پاس موجود سامان",recent:"حالیہ استعمال",accept:"وصولی کی تصدیق",reject:"مسترد",use:"استعمال درج کریں",none:"کوئی ریکارڈ نہیں",no_pending:"اسٹور کیپر سے ابھی کوئی حتمی سامان موصول نہیں ہوا",refresh:"تازہ کریں",purpose:"استعمال کا مقصد",location:"مقام",qty:"مقدار",notes:"نوٹس",save:"محفوظ کریں",reason:"مسترد کرنے کی وجہ",received:"وصول شدہ",remaining:"باقی"},
    hi:{dir:"ltr",title:"सफाई सामग्री",pending:"प्राप्ति की प्रतीक्षा",custody:"आपके पास सामग्री",recent:"हाल का उपयोग",accept:"प्राप्ति स्वीकार करें",reject:"अस्वीकार",use:"उपयोग दर्ज करें",none:"कोई रिकॉर्ड नहीं",no_pending:"स्टोरकीपर से अभी कोई पोस्ट की गई सामग्री नहीं आई है",refresh:"रीफ़्रेश",purpose:"उपयोग का उद्देश्य",location:"स्थान",qty:"मात्रा",notes:"टिप्पणी",save:"सहेजें",reason:"अस्वीकार कारण",received:"प्राप्त",remaining:"शेष"},
    id:{dir:"ltr",title:"Bahan Kebersihan",pending:"Menunggu penerimaan",custody:"Bahan dalam tanggung jawab Anda",recent:"Pemakaian terbaru",accept:"Terima",reject:"Tolak",use:"Catat pemakaian",none:"Tidak ada data",no_pending:"Belum ada bahan yang diposting dari petugas gudang",refresh:"Muat ulang",purpose:"Tujuan",location:"Lokasi",qty:"Jumlah",notes:"Catatan",save:"Simpan",reason:"Alasan penolakan",received:"Diterima",remaining:"Tersisa"},
    fr:{dir:"ltr",title:"Produits de nettoyage",pending:"En attente de réception",custody:"Produits sous votre garde",recent:"Utilisations récentes",accept:"Accepter",reject:"Refuser",use:"Enregistrer l’utilisation",none:"Aucune donnée",no_pending:"Aucun article validé n’est encore arrivé du magasinier",refresh:"Actualiser",purpose:"Objet",location:"Lieu",qty:"Quantité",notes:"Notes",save:"Enregistrer",reason:"Motif du refus",received:"Reçu",remaining:"Restant"},
    ha:{dir:"ltr",title:"Kayan Tsaftacewa",pending:"Ana jiran karɓa",custody:"Kayan da ke hannunka",recent:"Amfani na baya-bayan nan",accept:"Tabbatar da karɓa",reject:"Ƙi",use:"Rubuta amfani",none:"Babu bayanai",no_pending:"Babu kayan da aka kammala daga mai rumbu tukuna",refresh:"Sabunta",purpose:"Dalilin amfani",location:"Wuri",qty:"Adadi",notes:"Bayani",save:"Ajiye",reason:"Dalilin ƙin karɓa",received:"An karɓa",remaining:"Sauran"},
    sw:{dir:"ltr",title:"Vifaa vya Usafi",pending:"Vinasubiri kupokelewa",custody:"Vifaa ulivyo navyo",recent:"Matumizi ya hivi karibuni",accept:"Thibitisha kupokea",reject:"Kataa",use:"Rekodi matumizi",none:"Hakuna taarifa",no_pending:"Hakuna vifaa vilivyothibitishwa kutoka kwa mhifadhi bado",refresh:"Onyesha upya",purpose:"Sababu ya matumizi",location:"Eneo",qty:"Kiasi",notes:"Maelezo",save:"Hifadhi",reason:"Sababu ya kukataa",received:"Imepokelewa",remaining:"Iliyobaki"},
    uz:{dir:"ltr",title:"Tozalash materiallari",pending:"Qabul qilish kutilmoqda",custody:"Sizdagi materiallar",recent:"So‘nggi sarf",accept:"Qabul qilish",reject:"Rad etish",use:"Sarfni yozish",none:"Ma’lumot yo‘q",no_pending:"Omborchidan hali tasdiqlangan material kelmagan",refresh:"Yangilash",purpose:"Sarf maqsadi",location:"Joy",qty:"Miqdor",notes:"Izoh",save:"Saqlash",reason:"Rad etish sababi",received:"Qabul qilindi",remaining:"Qoldi"}
  };
  let lang = localStorage.getItem("wafd_lang") || "ar", data = {};
  const t = (key) => (dictionaries[lang] || dictionaries.en)[key] || dictionaries.en[key] || key;
  const localData = (value) => {
    const parts = String(value || "").split("/").map((part) => part.trim());
    return parts.length > 1 ? (lang === "ar" ? parts[0] : parts[parts.length - 1]) : String(value || "");
  };

  function shell() {
    page.set_title(t("title"));
    setTimeout(() => {
      page.set_title(t("title"));
      $(wrapper).find(".page-title .title-text").text(t("title"));
    }, 0);
    $root.attr("dir", t("dir")).html(`<style>.wafd-clean-head-actions{display:flex;gap:8px;align-items:center}.wafd-clean-head-actions button,.wafd-clean-section-refresh{border:1px solid #d2b566;background:transparent;color:inherit;border-radius:10px;padding:8px 11px}.wafd-clean-section-refresh{margin-inline-start:auto;color:#806527;font-size:12px}@media(max-width:600px){.wafd-clean-head-actions{flex-direction:column}.wafd-clean-head-actions button{display:none}}</style><div class="wafd-clean-wrap">
      <header><div><small>WAFD ONE</small><h2>${esc(t("title"))}</h2></div><div class="wafd-clean-head-actions"><button type="button" data-refresh>↻ ${esc(t("refresh"))}</button></div></header>
      <section><h3>${esc(t("pending"))}<b>${(data.pending||[]).length}</b><button type="button" class="wafd-clean-section-refresh" data-refresh>↻ ${esc(t("refresh"))}</button></h3><div class="wafd-clean-grid" id="clean-pending">${pendingCards()}</div></section>
      <section><h3>${esc(t("custody"))}<b>${(data.custody||[]).length}</b></h3><div class="wafd-clean-grid" id="clean-custody">${custodyCards()}</div></section>
      <section><h3>${esc(t("recent"))}</h3><div class="wafd-clean-list">${usageCards()}</div></section>
    </div>`);
    $root.off("change click");
    $root.on("click", "[data-accept]", function(){ respond($(this).data("accept"), "accept"); });
    $root.on("click", "[data-reject]", function(){ reject($(this).data("reject")); });
    $root.on("click", "[data-use]", function(){ record($(this).data("use")); });
    $root.on("click", "[data-refresh]", load);
  }
  function empty(){ return `<div class="wafd-clean-empty">${esc(t("none"))}</div>`; }
  function pendingCards(){ return !(data.pending||[]).length ? `<div class="wafd-clean-empty">${esc(t("no_pending"))}</div>` : data.pending.map(m=>`<article class="handover"><div class="tag">${esc(m.name)}</div><small>${esc(localData(m.source_warehouse))} · ${esc(m.posting_date)}</small>${m.items.map(i=>`<p><strong>${esc(i.ingredient_label || localData(i.ingredient))}</strong><span>${esc(i.quantity)} ${esc(localData(i.uom))}</span></p>`).join("")}<div class="buttons"><button class="primary" data-accept="${esc(m.name)}">✓ ${esc(t("accept"))}</button><button data-reject="${esc(m.name)}">× ${esc(t("reject"))}</button></div></article>`).join(""); }
  function custodyCards(){ return !(data.custody||[]).length ? empty() : data.custody.map((i,idx)=>`<article class="custody"><strong>${esc(i.ingredient_label || localData(i.ingredient))}</strong><div><span>${esc(t("received"))}: ${esc(i.received_quantity)} ${esc(localData(i.uom))}</span><b>${esc(t("remaining"))}: ${esc(i.remaining_quantity)} ${esc(localData(i.uom))}</b></div><button data-use="${idx}">− ${esc(t("use"))}</button></article>`).join(""); }
  function usageCards(){ return !(data.recent_usage||[]).length ? empty() : data.recent_usage.map(u=>`<article><div><b>${esc(localData(u.purpose))}</b><small>${esc(localData(u.location||""))} · ${esc(u.usage_date)}</small></div><span>${(u.items||[]).map(i=>`${esc(i.ingredient_label || localData(i.ingredient))}: ${esc(i.quantity)} ${esc(localData(i.uom))}`).join(lang === "ar" ? "، " : ", ")}</span></article>`).join(""); }
  function respond(name,action){ frappe.confirm(t("accept")+"؟",()=>frappe.call({method:"wafd_one.cleaning_portal.respond_cleaning_handover",args:{movement_name:name,action},freeze:true,callback:load})); }
  function reject(name){ const d=new frappe.ui.Dialog({title:t("reject"),fields:[{fieldname:"reason",fieldtype:"Small Text",label:t("reason"),reqd:1}],primary_action_label:t("reject"),primary_action(v){d.hide();frappe.call({method:"wafd_one.cleaning_portal.respond_cleaning_handover",args:{movement_name:name,action:"reject",rejection_reason:v.reason},freeze:true,callback:load});}});d.show(); }
  function record(index){ const item=(data.custody||[])[Number(index)]; if(!item)return; const d=new frappe.ui.Dialog({title:t("use"),fields:[{fieldtype:"Data",fieldname:"item",label:t("title"),default:item.ingredient_label || localData(item.ingredient),read_only:1},{fieldtype:"Float",fieldname:"quantity",label:`${t("qty")} (${localData(item.uom)})`,reqd:1},{fieldtype:"Data",fieldname:"purpose",label:t("purpose"),reqd:1},{fieldtype:"Data",fieldname:"location",label:t("location")},{fieldtype:"Small Text",fieldname:"notes",label:t("notes")}],primary_action_label:t("save"),primary_action(v){d.hide();frappe.call({method:"wafd_one.cleaning_portal.record_cleaning_usage",args:{source_handover:item.handover,ingredient:item.ingredient,quantity:v.quantity,purpose:v.purpose,location:v.location,notes:v.notes},freeze:true,callback:load});}});d.show(); }
  function load(){ frappe.call({method:"wafd_one.cleaning_portal.get_cleaning_dashboard",args:{language:lang},freeze:true,callback(r){data=r.message||{};shell();}}); }
  wrapper.wafdRefreshCleaning = load;
  wrapper.wafdApplyCleaningLanguage = function(){ lang=localStorage.getItem("wafd_lang")||"ar"; load(); };
  load();
};

frappe.pages["wafd-cleaning-home"].on_page_show = function(wrapper){
  wrapper.wafdApplyCleaningLanguage?.();
};
