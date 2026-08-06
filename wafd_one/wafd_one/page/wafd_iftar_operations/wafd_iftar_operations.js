frappe.pages["wafd-iftar-operations"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("تشغيل إفطار الصائم"), single_column: true });
  const $r = $(wrapper).find(".layout-main-section").attr("dir", "rtl").html(`
    <div class="io-wrap">
      <div class="io-top">
        <div><h2>لوحة التشغيل اليومية</h2><p>الإنتاج والتغليف والتحميل والتسليم والاستلام في شاشة واحدة</p></div>
        <div class="io-controls"><input type="date" class="form-control io-date"><button class="btn btn-primary io-new">مشروع جديد</button></div>
      </div>
      <div class="io-note"></div>
      <div class="io-kpis"></div>
      <div class="io-card"><div class="io-head"><h3>مشاريع اليوم</h3><button class="btn btn-default io-refresh">تحديث</button></div><div class="io-table"></div></div>
    </div>`);
  $r.find(".io-date").val(frappe.datetime.get_today());
  $r.on("click", ".io-new", () => frappe.set_route("wafd-iftar-wizard"));
  $r.on("click", ".io-refresh", () => load(false));
  $r.on("change", ".io-date", () => load(false));
  $r.on("click", "[data-op]", function () { frappe.set_route("Form", "WAFD Iftar Daily Operation", $(this).data("op")); });
  const num = v => frappe.format(Number(v || 0), { fieldtype: "Int" });
  let autoJumped = false;

  async function load(allowJump = true) {
    const selected = $r.find(".io-date").val();
    const response = await frappe.call({ method: "wafd_one.wafd_one.iftar_pro.get_dashboard", args: { date: selected }, freeze: true });
    const x = response.message || { summary: {}, rows: [] };
    if (allowJump && !x.rows.length && x.suggested_date && !autoJumped) {
      autoJumped = true;
      $r.find(".io-date").val(x.suggested_date);
      $r.find(".io-note").html(`<div class="alert alert-info">لا توجد عمليات في تاريخ اليوم؛ تم عرض أقرب يوم تشغيل تلقائياً.</div>`);
      return load(false);
    }
    const s = x.summary || {};
    const cards = [["مشاريع اليوم", s.project_count], ["الوجبات المطلوبة", s.planned_meals], ["تم الإنتاج", s.produced_meals], ["تم التغليف", s.packaged_meals], ["تم التحميل", s.loaded_meals], ["تم التسليم", s.delivered_meals], ["تم الاستلام", s.received_meals], ["المتبقي", s.remaining_meals], ["نسبة الإنجاز", `${s.completion_percent || 0}%`]];
    $r.find(".io-kpis").html(cards.map(c => `<div><span>${c[0]}</span><strong>${typeof c[1] === "number" ? num(c[1]) : c[1]}</strong></div>`).join(""));
    $r.find(".io-table").html(x.rows.length ? `<table class="table"><thead><tr><th>المشروع</th><th>الموقع</th><th>المخطط</th><th>الإنتاج</th><th>التغليف</th><th>التحميل</th><th>التسليم</th><th>الاستلام</th><th>الإنجاز</th></tr></thead><tbody>${x.rows.map(r => `<tr data-op="${r.name}"><td><b>${frappe.utils.escape_html(r.project_title || r.project)}</b><small>${frappe.utils.escape_html(r.project)}</small></td><td>${frappe.utils.escape_html(r.distribution_site || "")}</td><td>${num(r.planned_meals)}</td><td>${num(r.produced_meals)}</td><td>${num(r.packaged_meals)}</td><td>${num(r.loaded_meals)}</td><td>${num(r.delivered_meals)}</td><td>${num(r.received_meals)}</td><td><div class="progress"><div class="progress-bar" style="width:${r.completion_percent || 0}%"></div></div>${r.completion_percent || 0}%</td></tr>`).join("")}</tbody></table>` : `<div class="io-empty">لا توجد عمليات لهذا التاريخ. اختر تاريخ المشروع أو أنشئ مشروعاً جديداً.</div>`);
  }
  load(true);
  // Keep the command center current when supervisors update stages in other tabs/devices.
  const refreshTimer = setInterval(() => {
    if (!document.hidden) load(false);
  }, 15000);
  $(wrapper).on("remove", () => clearInterval(refreshTimer));
};
