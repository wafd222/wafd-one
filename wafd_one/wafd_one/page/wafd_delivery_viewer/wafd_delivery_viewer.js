frappe.pages["wafd-delivery-viewer"].on_page_load = function (wrapper) {
  const lang = localStorage.getItem("wafd_lang") || "ar";
  const ar = lang === "ar";
  const tr = (a, e) => ar ? a : e;
  const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
  const languages = {ar:"العربية",en:"English",id:"Bahasa Indonesia",ur:"اردو",hi:"हिन्दी",bn:"বাংলা",fr:"Français",ha:"Hausa",sw:"Kiswahili",uz:"O‘zbekcha"};
  const local = (v) => {
    const parts = String(v || "").split("/").map((x) => x.trim());
    return parts.length > 1 ? (ar ? parts[0] : parts[parts.length - 1]) : String(v || "—");
  };
  const fmt = (v) => v ? (frappe.datetime.str_to_user(v) || v) : tr("بانتظار التنفيذ", "Pending");
  const page = frappe.ui.make_app_page({parent: wrapper, title: tr("بيانات التسليم", "Delivery Data"), single_column: true});
  const $root = $(page.body).attr("dir", ar ? "rtl" : "ltr");

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

  function renderTrip(row) {
    const photo = row.has_delivery_photo
      ? `<img class="wafv-photo" loading="lazy" src="/api/method/wafd_one.delivery_tracking.get_my_delivery_photo?assignment_name=${encodeURIComponent(row.assignment_name)}" alt="${esc(tr("صورة التسليم", "Delivery photo"))}">`
      : `<div class="wafv-photo-empty">${esc(tr("لم ترفق صورة التسليم بعد", "Delivery photo is not available yet"))}</div>`;
    return `<article class="wafv-card">
      ${row.schedule_customer ? `<div class="wafv-customer"><small>${esc(tr("العميل", "Customer"))}</small><b>${esc(row.schedule_customer)}</b></div>` : ""}
      <div class="wafv-card-head"><div><small>${esc(tr("الجهة أو الفندق", "Destination"))}</small><h2>${esc(ar ? row.destination_name : (row.destination_name_en || row.destination_name))}</h2></div><span>${esc(local(row.status))}</span></div>
      <div class="wafv-grid">
        <div><small>${esc(tr("نوع الوجبة", "Meal"))}</small><b>${esc(local(row.meal_type))}</b></div>
        <div><small>${esc(tr("عدد الوجبات", "Meals"))}</small><b>${Number(row.quantity) > 0 ? esc(row.quantity) : esc(tr("غير محدد", "Not specified"))}</b></div>
        <div><small>${esc(tr("اسم السائق", "Driver"))}</small><b>${esc(row.driver_name || "—")}</b></div>
        <div><small>${esc(tr("رقم الجوال", "Mobile"))}</small><b dir="ltr">${esc(row.driver_mobile || "—")}</b></div>
        <div><small>${esc(tr("رقم اللوحة", "Plate number"))}</small><b>${esc(row.plate_number || "—")}</b></div>
        <div><small>${esc(tr("موعد التوصيل", "Scheduled delivery"))}</small><b>${esc(fmt(row.planned_arrival || row.trip_date))}</b></div>
      </div>
      <div class="wafv-timeline">
        ${[[tr("استلام السائق", "Driver accepted"), row.driver_accepted_on], [tr("وقت الخروج", "Departure"), row.departure_time], [tr("وقت الوصول", "Arrival"), row.arrival_time], [tr("التسليم", "Delivered"), row.delivery_time]].map(([label, value]) => `<div class="${value ? "done" : ""}"><i>${value ? "✓" : "•"}</i><span><b>${esc(label)}</b><small>${esc(fmt(value))}</small></span></div>`).join("")}
      </div>
      <div class="wafv-proof"><div><small>${esc(tr("اسم المستلم", "Receiver"))}</small><b>${esc(row.receiver_name || tr("بانتظار التسليم", "Pending delivery"))}</b></div>${photo}</div>
    </article>`;
  }

  async function load() {
    $root.html(`<div class="wafv-loading">${esc(tr("جارٍ تحميل بيانات التسليم…", "Loading delivery data…"))}</div>`);
    const response = await frappe.call({method: "wafd_one.delivery_tracking.get_my_delivery_tracking"});
    const result = response.message || {};
    const rows = result.trips || [];
    $root.html(`<style>
      .wafv-shell{max-width:900px;margin:16px auto 45px;padding:0 11px;color:#1d1e22}.wafv-hero{background:linear-gradient(135deg,#18191d,#28272b 67%,#59451f);color:#fff;border-radius:25px;padding:22px;margin-bottom:15px}.wafv-hero small{color:#e1c46e;font-weight:800}.wafv-hero h1{margin:5px 0;font-size:27px}.wafv-hero p{margin:0;color:#d3d3d5}.wafv-card{background:#fff;border:1px solid #e8e0d1;border-radius:22px;padding:18px;margin-bottom:14px;box-shadow:0 8px 24px rgba(22,23,27,.04)}.wafv-customer{display:flex;justify-content:space-between;align-items:center;gap:10px;background:#f8f2e4;border-radius:11px;padding:8px 11px;margin-bottom:12px;color:#765817}.wafv-customer small{color:#8b7b58}.wafv-card-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.wafv-card-head small,.wafv-grid small,.wafv-proof small{display:block;color:#777b82;margin-bottom:4px}.wafv-card-head h2{font-size:22px;margin:0}.wafv-card-head>span{background:#f1e8d5;color:#765817;border-radius:999px;padding:7px 11px;font-size:12px;font-weight:800}.wafv-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:16px}.wafv-grid>div,.wafv-proof>div:first-child{background:#faf9f6;border:1px solid #eee9df;border-radius:13px;padding:11px}.wafv-timeline{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:16px 0}.wafv-timeline>div{display:flex;gap:7px;align-items:center}.wafv-timeline i{width:27px;height:27px;border-radius:50%;background:#ece9e1;display:grid;place-items:center;font-style:normal}.wafv-timeline .done i{background:#28784b;color:#fff}.wafv-timeline b,.wafv-timeline small{display:block}.wafv-timeline small{color:#777b82;font-size:11px}.wafv-proof{display:grid;grid-template-columns:1fr 190px;gap:10px;align-items:stretch;border-top:1px solid #eee8dc;padding-top:14px}.wafv-photo{width:190px;height:125px;object-fit:cover;border-radius:13px;background:#eee}.wafv-photo-empty{display:grid;place-items:center;text-align:center;min-height:100px;border:1px dashed #d8d1c3;border-radius:13px;color:#87898e}.wafv-empty,.wafv-loading{text-align:center;padding:55px 16px;color:#777b82}
      @media(max-width:700px){.wafv-shell{padding:0 8px}.wafv-hero{margin:0 -8px 12px;border-radius:0 0 23px 23px}.wafv-grid{grid-template-columns:1fr 1fr}.wafv-timeline{grid-template-columns:1fr 1fr}.wafv-proof{grid-template-columns:1fr}.wafv-photo{width:100%;height:210px}}
    </style><section class="wafd-pwa-appbar" aria-label="WAFD ONE"><button type="button" class="wafd-pwa-menu-btn" aria-label="${esc(tr("القائمة", "Menu"))}" aria-expanded="false"><span></span><span></span><span></span></button><strong>WAFD ONE</strong><div class="wafd-pwa-menu" role="menu" hidden><label class="wafd-pwa-language-row" for="wafv-language"><span>文 ${esc(tr("اللغة", "Language"))}</span><select id="wafv-language">${Object.entries(languages).map(([code,name])=>`<option value="${code}" ${code===lang?"selected":""}>${esc(name)}</option>`).join("")}</select></label><button type="button" class="is-danger" data-wafv-logout>↪ <span>${esc(tr("تسجيل الخروج", "Logout"))}</span></button></div></section><main class="wafv-shell"><section class="wafv-hero"><small>WAFD ONE</small><h1>${esc(tr("بيانات التسليم", "Delivery Data"))}</h1><p>${esc(result.viewer_name || "")}</p><p>${esc(tr("شاشة للقراءة فقط — لا يمكن الإضافة أو التعديل", "Read-only screen — editing is disabled"))}</p></section><section>${rows.length ? rows.map(renderTrip).join("") : `<div class="wafv-card wafv-empty">${esc(tr("لا توجد عمليات تسليم مسندة إلى حسابك حاليًا.", "No deliveries are assigned to your account."))}</div>`}</section></main>`);
    bindViewerMenu();
  }

  wrapper.wafdDeliveryViewerLoad = load;
  load();
};

frappe.pages["wafd-delivery-viewer"].on_page_show = function (wrapper) {
  wrapper.wafdDeliveryViewerLoad?.();
};
