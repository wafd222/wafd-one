frappe.pages["wafd-one-dashboard"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("WAFD ONE"), single_column: true });
  const $root = $(wrapper).find(".layout-main-section").attr("dir", "rtl");
  const today = frappe.datetime.get_today();
  const currentUser = frappe.user.full_name() || frappe.session.user;

  $root.html(`
    <div class="wafd-command-center">
      <section class="wafd-hero-pro">
        <div class="wafd-hero-copy">
          <div class="wafd-logo-shell"><img src="/assets/wafd_one/images/wafd-almadinah-dashboard.png" alt="WAFD ONE"></div>
          <div>
            <span class="wafd-eyebrow">شركة وفد المدينة لخدمات الإعاشة</span>
            <h1>WAFD ONE <small>Operations Command Center</small></h1>
            <p>لوحة موحدة لإدارة دورة الإعاشة من العقد والتخطيط حتى التسليم والتحصيل.</p>
          </div>
        </div>
        <div class="wafd-hero-side">
          <div class="wafd-user-card"><span>المستخدم</span><strong>${frappe.utils.escape_html(currentUser)}</strong></div>
          <div class="wafd-user-card"><span>التاريخ</span><strong>${frappe.datetime.str_to_user(today)}</strong></div>
          <button class="wafd-ghost-btn" data-route="wafd-launch-center">فحص الجاهزية</button>
        </div>
      </section>

      <section class="wafd-action-grid">
        <button class="wafd-action wafd-action-primary" data-new="WAFD Contract"><b>＋</b><span>بدء عقد جديد</span><small>إنشاء دورة تشغيل متكاملة</small></button>
        <button class="wafd-action" data-new="WAFD Daily Meal Plan"><b>◫</b><span>خطة الوجبات اليومية</span><small>تخطيط الكميات والفنادق</small></button>
        <button class="wafd-action" data-new="WAFD Hotel Undertaking"><b>✦</b><span>إنشاء تعهد فندق</span><small>تعهد مستقل جاهز للطباعة</small></button>
        <button class="wafd-action" data-list="WAFD Hotel Undertaking"><b>▤</b><span>تعهدات الفنادق</span><small>عرض وطباعة التعهدات</small></button>
        <button class="wafd-action" data-list="WAFD Invoice"><b>ر.س</b><span>الفواتير</span><small>المستحقات وحالة الفوترة</small></button>
        <button class="wafd-action" data-list="WAFD Payment"><b>✓</b><span>التحصيلات</span><small>الدفعات والأرصدة</small></button>
      </section>

      <section class="wafd-control-strip">
        <div class="wafd-control-title"><span>الفترة التشغيلية</span><small>تحديث المؤشرات والمشاريع حسب التاريخ</small></div>
        <label>من<input type="date" class="form-control wafd-from"></label>
        <label>إلى<input type="date" class="form-control wafd-to"></label>
        <button class="wafd-refresh">تحديث البيانات</button>
      </section>

      <section class="wafd-section-head"><div><span>مسار التشغيل المتكامل</span><small>افتح أي مرحلة مباشرة</small></div></section>
      <section class="wafd-flow-pro"></section>

      <section class="wafd-section-head"><div><span>مؤشرات الأداء</span><small>نظرة سريعة على التشغيل والمالية</small></div></section>
      <section class="wafd-kpi-grid"></section>

      <section class="wafd-dashboard-grid">
        <article class="wafd-card wafd-project-card">
          <div class="wafd-card-head"><div><h3>المشاريع الحالية</h3><small>التقدم والمرحلة التالية</small></div><button data-list="WAFD Catering Project">عرض الكل</button></div>
          <div class="wafd-projects"></div>
        </article>
        <article class="wafd-card">
          <div class="wafd-card-head"><div><h3>تنبيهات تحتاج متابعة</h3><small>الأولوية التشغيلية اليوم</small></div></div>
          <div class="wafd-alerts-pro"></div>
        </article>
      </section>

      <section class="wafd-dashboard-grid wafd-bottom-grid">
        <article class="wafd-card">
          <div class="wafd-card-head"><div><h3>التوصيلات القادمة</h3><small>الرحلات والفنادق والكميات</small></div><button data-list="WAFD Delivery Trip">عرض الكل</button></div>
          <div class="wafd-deliveries"></div>
        </article>
        <article class="wafd-card">
          <div class="wafd-card-head"><div><h3>وصول سريع</h3><small>المخزون والمستندات الأساسية</small></div></div>
          <div class="wafd-shortcuts">
            <button class="wafd-stock-receipt-shortcut" data-stock-receipt="1">استلام مواد مشتراة</button>
            <button data-list="WAFD Warehouse">المستودعات والثلاجات</button>
            <button data-list="WAFD Stock Movement">حركات المخزون</button>
            <button data-list="WAFD Production Batch">دفعات الإنتاج</button>
            <button data-list="WAFD Delivery Proof">إثباتات التسليم</button>
            <button data-list="WAFD Hotel">الفنادق</button>
            <button data-list="WAFD Recipe">الوصفات</button>
          </div>
        </article>
      </section>

      <section class="wafd-section-head"><div><span>لوحة المدير التنفيذية</span><small>المخاطر والأداء والربحية في شاشة واحدة</small></div></section>
      <section class="wafd-executive-grid">
        <article class="wafd-card">
          <div class="wafd-card-head"><div><h3>المخاطر الإدارية</h3><small>العقود والوثائق والربحية والتنبيهات</small></div><button class="wafd-refresh-alerts">تحديث التنبيهات</button></div>
          <div class="wafd-risk-grid"></div>
        </article>
        <article class="wafd-card">
          <div class="wafd-card-head"><div><h3>أفضل المشاريع</h3><small>الإيراد والربح والهامش</small></div><button data-list="WAFD Catering Project">عرض الكل</button></div>
          <div class="wafd-project-rankings"></div>
        </article>
      </section>

      <section class="wafd-executive-grid wafd-executive-secondary">
        <article class="wafd-card">
          <div class="wafd-card-head"><div><h3>أداء التوصيل</h3><small>السائقون والالتزام بالمواعيد</small></div><button data-list="WAFD Delivery Trip">الرحلات</button></div>
          <div class="wafd-driver-performance"></div>
        </article>
        <article class="wafd-card">
          <div class="wafd-card-head"><div><h3>أداء الفنادق</h3><small>الكميات المقبولة والمرفوضة</small></div><button data-list="WAFD Hotel">الفنادق</button></div>
          <div class="wafd-hotel-performance"></div>
        </article>
      </section>
    </div>`);

  $root.find(".wafd-to").val(today);
  $root.find(".wafd-from").val(frappe.datetime.add_days(today, -29));

  const flow = [
    ["01", "العقد", "WAFD Contract"], ["02", "المشروع", "WAFD Catering Project"],
    ["03", "الخطة اليومية", "WAFD Daily Meal Plan"], ["04", "الإنتاج", "WAFD Production Batch"],
    ["05", "الجودة", "WAFD Quality Inspection"], ["06", "التغليف", "WAFD Packaging Record"],
    ["07", "التحميل", "WAFD Loading Record"], ["08", "التوصيل", "WAFD Delivery Trip"],
    ["09", "الفاتورة", "WAFD Invoice"], ["10", "التحصيل", "WAFD Payment"]
  ];
  $root.find(".wafd-flow-pro").html(flow.map((item, index) => `
    <button data-list="${item[2]}"><i>${item[0]}</i><span>${item[1]}</span>${index < flow.length - 1 ? "<em>←</em>" : ""}</button>
  `).join(""));

  $root.on("click", "[data-route]", function () { frappe.set_route($(this).data("route")); });
  $root.on("click", "[data-stock-receipt]", function () {
    frappe.new_doc("WAFD Stock Movement", {
      movement_type: "استلام / Receipt",
      posting_date: frappe.datetime.now_datetime(),
      status: "مسودة / Draft",
      reference_type: "شراء مباشر / Direct Purchase",
      notes: "استلام مواد مشتراة وتوريدها إلى مستودعات أو ثلاجات الإعاشة"
    });
  });
  $root.on("click", "[data-new]", function () { frappe.new_doc($(this).data("new")); });
  $root.on("click", "[data-list]", function () { frappe.set_route("List", $(this).data("list")); });
  $root.on("click", "[data-docname]", function () { frappe.set_route("Form", $(this).data("doctype"), $(this).data("docname")); });
  $root.on("click", ".wafd-refresh", load);
  $root.on("click", ".wafd-refresh-alerts", function () {
    frappe.call({
      method: "wafd_one.executive.refresh_executive_alerts",
      freeze: true,
      freeze_message: __("جارٍ تحديث التنبيهات الإدارية...")
    }).then(() => { frappe.show_alert({ message: __("تم تحديث التنبيهات"), indicator: "green" }); load(); });
  });

  function escape(value) { return frappe.utils.escape_html(String(value ?? "")); }
  function money(value) { return format_currency(value || 0, "SAR"); }
  function empty(message) { return `<div class="wafd-empty">${escape(message)}</div>`; }

  function load() {
    frappe.call({
      method: "wafd_one.executive.get_executive_dashboard_data",
      args: { from_date: $root.find(".wafd-from").val(), to_date: $root.find(".wafd-to").val() },
      freeze: true,
      freeze_message: __("جارٍ تحديث مركز العمليات...")
    }).then((response) => render(response.message || {}));
  }

  function render(data) {
    const kpis = [
      ["المشاريع النشطة", data.active_projects || 0, "تشغيل", "WAFD Catering Project"],
      ["الوجبات المخططة", data.planned_meals || 0, "تخطيط", "WAFD Daily Meal Plan"],
      ["الوجبات المسلّمة", data.delivered_meals || 0, "توصيل", "WAFD Delivery Proof"],
      ["المستحقات القائمة", money(data.receivables), "مالي", "WAFD Invoice"]
    ];
    $root.find(".wafd-kpi-grid").html(kpis.map((item) => `
      <button data-list="${item[3]}"><small>${item[2]}</small><span>${item[0]}</span><strong>${escape(item[1])}</strong><i>عرض التفاصيل ←</i></button>
    `).join(""));

    const alertsData = data.alerts || {};
    const alerts = [
      ["عجز مواد", alertsData.material_shortages || 0, "WAFD Production Batch"],
      ["جودة مرفوضة", alertsData.quality_rejected || 0, "WAFD Quality Inspection"],
      ["رحلات متأخرة", alertsData.late_trips || 0, "WAFD Delivery Trip"],
      ["فواتير متأخرة", alertsData.overdue_invoices || 0, "WAFD Invoice"]
    ];
    $root.find(".wafd-alerts-pro").html(alerts.map((item) => `
      <button class="${item[1] ? "is-hot" : ""}" data-list="${item[2]}"><span>${item[0]}</span><b>${item[1]}</b><small>${item[1] ? "تحتاج إجراء" : "لا توجد ملاحظات"}</small></button>
    `).join(""));

    const projects = data.projects || [];
    $root.find(".wafd-projects").html(projects.length ? `<table><thead><tr><th>المشروع</th><th>التقدم</th><th>المسلّم</th></tr></thead><tbody>${projects.slice(0, 7).map((row) => `
      <tr data-doctype="WAFD Catering Project" data-docname="${escape(row.name)}"><td><b>${escape(row.project_name || row.name)}</b><small>${escape(row.name)}</small></td><td><div class="wafd-progress"><i style="width:${Math.min(100, flt(row.progress_percent || 0))}%"></i></div><span>${flt(row.progress_percent || 0).toFixed(0)}%</span></td><td>${escape(row.delivered_meals || 0)} / ${escape(row.total_meals || 0)}</td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد مشاريع حالية ضمن الفترة المحددة."));

    const deliveries = data.upcoming_deliveries || [];
    $root.find(".wafd-deliveries").html(deliveries.length ? `<table><thead><tr><th>التاريخ</th><th>الفندق</th><th>الكمية</th></tr></thead><tbody>${deliveries.slice(0, 7).map((row) => `
      <tr data-doctype="WAFD Delivery Trip" data-docname="${escape(row.name)}"><td>${escape(row.trip_date)}</td><td>${escape(row.hotel)}</td><td><b>${escape(row.quantity)}</b></td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد توصيلات قادمة."));

    const risks = data.executive_risks || {};
    const riskCards = [
      ["التنبيهات المفتوحة", risks.open_alerts || 0, "WAFD Operations Alert"],
      ["التنبيهات الحرجة", risks.critical_alerts || 0, "WAFD Operations Alert"],
      ["مشاريع هامشها منخفض", risks.low_margin_projects || 0, "WAFD Catering Project"],
      ["عقود تنتهي خلال 30 يومًا", risks.expiring_contracts || 0, "WAFD Contract"],
      ["وثائق مركبات قاربت الانتهاء", risks.vehicle_documents_expiring || 0, "WAFD Vehicle"],
      ["رخص سائقين قاربت الانتهاء", risks.driver_licenses_expiring || 0, "WAFD Driver"]
    ];
    $root.find(".wafd-risk-grid").html(riskCards.map((item) => `
      <button class="${item[1] ? "is-risk" : ""}" data-list="${item[2]}"><span>${item[0]}</span><strong>${escape(item[1])}</strong></button>
    `).join(""));

    const rankings = data.project_rankings || [];
    $root.find(".wafd-project-rankings").html(rankings.length ? `<table><thead><tr><th>المشروع</th><th>الربح</th><th>الهامش</th></tr></thead><tbody>${rankings.slice(0, 6).map((row) => `
      <tr data-doctype="WAFD Catering Project" data-docname="${escape(row.name)}"><td><b>${escape(row.project_name || row.name)}</b><small>${escape(row.primary_hotel || "")}</small></td><td>${money(row.profit)}</td><td>${flt(row.profit_margin_percent || 0).toFixed(1)}%</td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد بيانات ربحية كافية بعد."));

    const drivers = data.driver_performance || [];
    $root.find(".wafd-driver-performance").html(drivers.length ? `<table><thead><tr><th>السائق</th><th>الرحلات</th><th>في الوقت</th><th>متأخرة</th></tr></thead><tbody>${drivers.slice(0, 6).map((row) => `
      <tr><td><b>${escape(row.driver)}</b></td><td>${escape(row.trips || 0)}</td><td>${escape(row.on_time_trips || 0)}</td><td>${escape(row.delayed_trips || 0)}</td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد بيانات توصيل كافية بعد."));

    const hotels = data.hotel_performance || [];
    $root.find(".wafd-hotel-performance").html(hotels.length ? `<table><thead><tr><th>الفندق</th><th>التسليمات</th><th>المقبول</th><th>نسبة القبول</th></tr></thead><tbody>${hotels.slice(0, 6).map((row) => `
      <tr><td><b>${escape(row.hotel)}</b></td><td>${escape(row.deliveries || 0)}</td><td>${escape(row.accepted_quantity || 0)}</td><td>${flt(row.acceptance_percent || 0).toFixed(1)}%</td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد بيانات استلام كافية بعد."));
  }

  load();
};
