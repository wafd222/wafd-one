frappe.pages["wafd-one-dashboard"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("WAFD ONE"), single_column: true });
  const $root = $(wrapper).find(".layout-main-section").attr("dir", "rtl");
  const today = frappe.datetime.get_today();
  const currentUser = frappe.user.full_name() || frappe.session.user;

  $root.html(`
    <div class="wafd-dashboard wafd-dashboard-final">
      <section class="wafd-hero">
        <div class="wafd-brand">
          <img src="/assets/wafd_one/images/wafd-almadinah-official.png" alt="WAFD ONE">
          <div>
            <span>شركة وفد المدينة لخدمات الإعاشة</span>
            <h1>WAFD ONE</h1>
            <p>لوحة تشغيل يومية مبسطة من العقد حتى التحصيل.</p>
          </div>
        </div>
        <div class="wafd-hero-meta">
          <div><small>المستخدم</small><b>${frappe.utils.escape_html(currentUser)}</b></div>
          <div><small>التاريخ</small><b>${frappe.datetime.str_to_user(today)}</b></div>
          <button class="btn btn-light" data-route="wafd-launch-center">فحص الجاهزية</button>
        </div>
      </section>

      <section class="wafd-primary-actions">
        <button data-new="WAFD Contract"><span>عقد جديد</span><small>بدء دورة تشغيل</small></button>
        <button data-new="WAFD Catering Project"><span>مشروع جديد</span><small>إدارة المشروع</small></button>
        <button data-new="WAFD Daily Meal Plan"><span>خطة يومية</span><small>تخطيط الوجبات</small></button>
        <button data-new="WAFD Delivery Trip"><span>رحلة توصيل</span><small>التسليم والمتابعة</small></button>
      </section>

      <section class="wafd-toolbar">
        <div><b>الفترة التشغيلية</b><small>تحديث المؤشرات حسب التاريخ</small></div>
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
        <article><div class="panel-head"><h3>المشاريع الحالية</h3><button data-list="WAFD Catering Project">عرض الكل</button></div><div class="wafd-projects"></div></article>
        <article><div class="panel-head"><h3>التوصيلات القادمة</h3><button data-list="WAFD Delivery Trip">عرض الكل</button></div><div class="wafd-deliveries"></div></article>
      </section>
    </div>`);

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
      ["الوجبات المسلّمة", data.delivered_meals || 0, "توصيل"],
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
    $root.find(".wafd-projects").html(projects.length ? `<table><tr><th>المشروع</th><th>التقدم</th><th>المسلّم</th></tr>${projects.slice(0, 6).map((row) => `
      <tr data-doctype="WAFD Catering Project" data-docname="${escape(row.name)}"><td>${escape(row.project_name || row.name)}</td><td><div class="bar"><i style="width:${Math.min(100, flt(row.progress_percent || 0))}%"></i></div>${flt(row.progress_percent || 0).toFixed(0)}%</td><td>${escape(row.delivered_meals || 0)} / ${escape(row.total_meals || 0)}</td></tr>
    `).join("")}</table>` : empty("لا توجد مشاريع حالية."));

    const deliveries = data.upcoming_deliveries || [];
    $root.find(".wafd-deliveries").html(deliveries.length ? `<table><tr><th>التاريخ</th><th>الفندق</th><th>الكمية</th></tr>${deliveries.slice(0, 6).map((row) => `
      <tr data-doctype="WAFD Delivery Trip" data-docname="${escape(row.name)}"><td>${escape(row.trip_date)}</td><td>${escape(row.hotel)}</td><td>${escape(row.quantity)}</td></tr>
    `).join("")}</table>` : empty("لا توجد توصيلات قادمة."));
  }

  load();
};
