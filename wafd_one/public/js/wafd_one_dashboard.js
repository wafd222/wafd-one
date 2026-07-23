frappe.pages["wafd-one-dashboard"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("WAFD ONE"), single_column: true });
  const $root = $(wrapper).find(".layout-main-section").attr("dir", "rtl");

  $root.html(`
    <div class="wafd-dashboard wafd-dashboard-final">
      <section class="wafd-hero">
        <div class="wafd-brand">
          <img src="/assets/wafd_one/images/wafd-almadinah-official.png" alt="WAFD ONE">
          <div>
            <span>إدارة وتشغيل خدمات الإعاشة</span>
            <h1>WAFD ONE</h1>
            <p>لوحة يومية مبسطة من العقد حتى التحصيل.</p>
          </div>
        </div>
        <div class="wafd-hero-actions">
          <button class="btn btn-light" data-route="wafd-launch-center">فحص الجاهزية</button>
          <button class="btn btn-light" data-new="WAFD Contract">عقد جديد</button>
          <button class="btn btn-gold" data-new="WAFD Catering Project">مشروع جديد</button>
        </div>
      </section>

      <section class="wafd-quick wafd-quick-final">
        <button data-new="WAFD Daily Meal Plan">+ خطة يومية</button>
        <button data-new="WAFD Production Batch">+ دفعة إنتاج</button>
        <button data-new="WAFD Delivery Trip">+ رحلة توصيل</button>
        <button data-new="WAFD Invoice">+ فاتورة</button>
      </section>

      <section class="wafd-filter">
        <div><b>الفترة التشغيلية</b><small>عرض مؤشرات الفترة المحددة</small></div>
        <input type="date" class="form-control wafd-from">
        <input type="date" class="form-control wafd-to">
        <button class="btn btn-dark wafd-refresh">تحديث</button>
      </section>

      <div class="wafd-title">مسار التشغيل</div>
      <section class="wafd-flow"></section>

      <div class="wafd-title">ملخص الأداء</div>
      <section class="wafd-kpis"></section>

      <div class="wafd-title">تنبيهات تحتاج متابعة</div>
      <section class="wafd-alerts"></section>

      <section class="wafd-panels wafd-panels-final">
        <article><h3>المشاريع الحالية</h3><div class="wafd-projects"></div></article>
        <article><h3>التوصيلات القادمة</h3><div class="wafd-deliveries"></div></article>
        <article><h3>الفواتير المتأخرة</h3><div class="wafd-invoices"></div></article>
      </section>

      <div class="wafd-title">الوحدات الأساسية</div>
      <section class="wafd-grid wafd-grid-final"></section>
    </div>`);

  const today = frappe.datetime.get_today();
  $root.find(".wafd-to").val(today);
  $root.find(".wafd-from").val(frappe.datetime.add_days(today, -29));

  const flow = [
    ["1", "العقد", "WAFD Contract"],
    ["2", "المشروع", "WAFD Catering Project"],
    ["3", "الخطة اليومية", "WAFD Daily Meal Plan"],
    ["4", "الإنتاج والجودة", "WAFD Production Batch"],
    ["5", "التغليف والتحميل", "WAFD Packaging Record"],
    ["6", "التوصيل", "WAFD Delivery Trip"],
    ["7", "الفاتورة والتحصيل", "WAFD Invoice"],
  ];
  $root.find(".wafd-flow").html(flow.map((item, index) => `
    <button data-list="${item[2]}"><i>${item[0]}</i><span>${item[1]}</span>${index < flow.length - 1 ? "<em>←</em>" : ""}</button>
  `).join(""));

  const units = [
    ["العقود", "WAFD Contract"], ["المشاريع", "WAFD Catering Project"],
    ["الخطط اليومية", "WAFD Daily Meal Plan"], ["دفعات الإنتاج", "WAFD Production Batch"],
    ["فحص الجودة", "WAFD Quality Inspection"], ["التغليف", "WAFD Packaging Record"],
    ["التحميل", "WAFD Loading Record"], ["رحلات التوصيل", "WAFD Delivery Trip"],
    ["الفواتير", "WAFD Invoice"], ["التحصيلات", "WAFD Payment"],
    ["الفنادق", "WAFD Hotel"], ["الوصفات", "WAFD Recipe"],
  ];
  $root.find(".wafd-grid").html(units.map((item) => `
    <button data-list="${item[1]}"><span>${item[0]}</span><b>فتح</b></button>
  `).join(""));

  $root.on("click", "[data-route]", function () { frappe.set_route($(this).data("route")); });
  $root.on("click", "[data-new]", function () { frappe.new_doc($(this).data("new")); });
  $root.on("click", "[data-list]", function () { frappe.set_route("List", $(this).data("list")); });
  $root.on("click", "[data-docname]", function () { frappe.set_route("Form", $(this).data("doctype"), $(this).data("docname")); });
  $root.on("click", ".wafd-refresh", load);

  function escape(value) { return frappe.utils.escape_html(String(value ?? "")); }
  function money(value) { return format_currency(value || 0, "SAR"); }
  function empty(message) { return `<div class="wafd-empty">${escape(message)}</div>`; }

  function load() {
    frappe.call({
      method: "wafd_one.executive.get_executive_dashboard_data",
      args: { from_date: $root.find(".wafd-from").val(), to_date: $root.find(".wafd-to").val() },
      freeze: true,
      freeze_message: __("جاري تحديث لوحة التشغيل...")
    }).then((response) => render(response.message || {}));
  }

  function render(data) {
    const kpis = [
      ["المشاريع النشطة", data.active_projects || 0, "تشغيل"],
      ["الوجبات المخططة", data.planned_meals || 0, "تخطيط"],
      ["الوجبات المنتجة", data.produced_meals || 0, "إنتاج"],
      ["الوجبات المسلّمة", data.delivered_meals || 0, "توصيل"],
      ["نسبة التسليم", `${flt(data.delivery_rate || 0).toFixed(1)}%`, "أداء"],
      ["المستحقات", money(data.receivables), "مالي"],
    ];
    $root.find(".wafd-kpis").html(kpis.map((item) => `
      <div><small>${item[2]}</small><span>${item[0]}</span><strong>${escape(item[1])}</strong></div>
    `).join(""));

    const alertsData = data.alerts || {};
    const alerts = [
      ["عجز مواد", alertsData.material_shortages || 0, "WAFD Production Batch"],
      ["جودة مرفوضة", alertsData.quality_rejected || 0, "WAFD Quality Inspection"],
      ["رحلات متأخرة", alertsData.late_trips || 0, "WAFD Delivery Trip"],
      ["فواتير متأخرة", alertsData.overdue_invoices || 0, "WAFD Invoice"],
    ];
    $root.find(".wafd-alerts").html(alerts.map((item) => `
      <button class="${item[1] ? "hot" : ""}" data-list="${item[2]}"><span>${item[0]}</span><b>${item[1]}</b></button>
    `).join(""));

    const projects = data.projects || [];
    $root.find(".wafd-projects").html(projects.length ? `<table><tr><th>المشروع</th><th>التقدم</th><th>المسلّم</th></tr>${projects.slice(0, 8).map((row) => `
      <tr data-doctype="WAFD Catering Project" data-docname="${escape(row.name)}"><td>${escape(row.project_name || row.name)}</td><td><div class="bar"><i style="width:${Math.min(100, flt(row.progress_percent || 0))}%"></i></div>${flt(row.progress_percent || 0).toFixed(0)}%</td><td>${escape(row.delivered_meals || 0)} / ${escape(row.total_meals || 0)}</td></tr>
    `).join("")}</table>` : empty("لا توجد مشاريع حالية."));

    const deliveries = data.upcoming_deliveries || [];
    $root.find(".wafd-deliveries").html(deliveries.length ? `<table><tr><th>التاريخ</th><th>الفندق</th><th>الكمية</th></tr>${deliveries.slice(0, 8).map((row) => `
      <tr data-doctype="WAFD Delivery Trip" data-docname="${escape(row.name)}"><td>${escape(row.trip_date)}</td><td>${escape(row.hotel)}</td><td>${escape(row.quantity)}</td></tr>
    `).join("")}</table>` : empty("لا توجد توصيلات قادمة."));

    const invoices = data.overdue_invoices || [];
    $root.find(".wafd-invoices").html(invoices.length ? `<table><tr><th>الفاتورة</th><th>الاستحقاق</th><th>الرصيد</th></tr>${invoices.slice(0, 8).map((row) => `
      <tr data-doctype="WAFD Invoice" data-docname="${escape(row.name)}"><td>${escape(row.name)}</td><td>${escape(row.due_date)}</td><td>${money(row.balance)}</td></tr>
    `).join("")}</table>` : empty("لا توجد فواتير متأخرة."));
  }

  load();
};
