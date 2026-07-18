frappe.pages["wafd-one-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({ parent: wrapper, title: __("WAFD ONE"), single_column: true });
  const $root = $(wrapper).find(".layout-main-section");
  $root.attr("dir", "rtl").html(`
    <div class="wafd-dashboard">
      <div class="wafd-hero"><div><h2>WAFD ONE</h2><p>لوحة القيادة التنفيذية لعمليات الإعاشة.</p></div><div class="wafd-admin-entry" style="display:none"><button class="btn btn-default wafd-open-administration">إدارة WAFD ONE</button></div></div>
      <div class="wafd-toolbar">
        <div><label>من</label><input type="date" class="form-control wafd-from-date"></div>
        <div><label>إلى</label><input type="date" class="form-control wafd-to-date"></div>
        <button class="btn btn-primary wafd-refresh">تحديث</button>
      </div>
      <div class="wafd-section-title">المؤشرات التنفيذية</div><div class="wafd-kpis"></div>
      <div class="wafd-section-title">التنبيهات التي تحتاج إجراء</div><div class="wafd-alerts"></div>
      <div class="wafd-panels">
        <section><h4>المشاريع</h4><div class="wafd-projects"></div></section>
        <section><h4>التوصيلات القادمة</h4><div class="wafd-deliveries"></div></section>
        <section><h4>الفواتير المتأخرة</h4><div class="wafd-invoices"></div></section>
      </div>
      <div class="wafd-section-title">العمليات الرئيسية</div><div class="wafd-grid"></div>
    </div>`);

  const can_administer = frappe.session.user === "Administrator" || (frappe.user_roles || []).includes("System Manager");
  if (can_administer) {
    $root.find(".wafd-admin-entry").show();
  }
  $root.on("click", ".wafd-open-administration", function () {
    frappe.set_route("wafd-administration");
  });

  const today = frappe.datetime.get_today();
  $root.find(".wafd-to-date").val(today);
  $root.find(".wafd-from-date").val(frappe.datetime.add_days(today, -29));

  const items = [
    ["المشاريع", "WAFD Catering Project", "octicon-project"], ["البعثات والعملاء", "WAFD Mission", "octicon-people"],
    ["الفنادق", "WAFD Hotel", "octicon-home"], ["العقود", "WAFD Contract", "octicon-file"],
    ["خطط الوجبات", "WAFD Meal Plan", "octicon-checklist"], ["دفعات الإنتاج", "WAFD Production Batch", "octicon-gear"],
    ["فحص الجودة", "WAFD Quality Inspection", "octicon-shield"], ["التغليف", "WAFD Packaging Record", "octicon-package"],
    ["التحميل", "WAFD Loading Record", "octicon-package"], ["رحلات التوصيل", "WAFD Delivery Trip", "octicon-location"],
    ["إثبات التسليم", "WAFD Delivery Proof", "octicon-device-camera"], ["حركة المخزون", "WAFD Stock Movement", "octicon-sync"],
    ["أوامر الشراء", "WAFD Purchase Order", "octicon-cart"], ["الفواتير", "WAFD Invoice", "octicon-file-text"],
    ["التحصيلات", "WAFD Payment", "octicon-check"], ["تكاليف المشاريع", "WAFD Project Cost", "octicon-graph"]
  ];
  const $grid = $root.find(".wafd-grid");
  items.forEach(([label, doctype, icon]) => $grid.append(`<button class="wafd-card" data-doctype="${frappe.utils.escape_html(doctype)}"><span class="wafd-card-icon octicon ${icon}"></span><span class="wafd-card-label">${label}</span><span class="wafd-card-arrow">‹</span></button>`));
  if (can_administer) {
    $grid.append(`<button class="wafd-card wafd-open-administration"><span class="wafd-card-icon octicon octicon-gear"></span><span class="wafd-card-label">إدارة WAFD ONE</span><span class="wafd-card-arrow">‹</span></button>`);
  }

  $root.on("click", ".wafd-card", function () { frappe.set_route("List", $(this).data("doctype")); });
  $root.on("click", "[data-route-doctype]", function () { frappe.set_route("List", $(this).data("route-doctype")); });
  $root.on("click", "[data-docname]", function () { frappe.set_route("Form", $(this).data("doctype"), $(this).data("docname")); });
  $root.on("click", ".wafd-refresh", load_dashboard);

  function money(value) { return format_currency(value || 0, "SAR"); }
  function esc(value) { return frappe.utils.escape_html(String(value == null ? "" : value)); }
  function empty(text) { return `<div class="wafd-empty">${esc(text)}</div>`; }
  function status(text) { return `<span class="wafd-status">${esc(text || "-")}</span>`; }

  function load_dashboard() {
    frappe.call({
      method: "wafd_one.finance.get_dashboard_data",
      args: { from_date: $root.find(".wafd-from-date").val(), to_date: $root.find(".wafd-to-date").val() },
      freeze: true,
      freeze_message: __("جاري تحديث لوحة القيادة..."),
    }).then(r => render(r.message || {}));
  }

  function render(d) {
    const kpis = [
      ["إجمالي المشاريع", d.active_projects || 0], ["الوجبات المخططة", d.planned_meals || 0],
      ["الوجبات المنتجة", d.produced_meals || 0], ["الوجبات المستلمة", d.delivered_meals || 0],
      ["نسبة التسليم", `${flt(d.delivery_rate || 0).toFixed(1)}%`], ["المرفوض", d.rejected_meals || 0],
      ["إجمالي الفواتير", money(d.invoiced_revenue)], ["الإيراد المحصل", money(d.collected_revenue)], ["التكلفة", money(d.actual_cost)],
      ["الربح", money(d.profit)], ["المستحقات", money(d.receivables)]
    ];
    $root.find(".wafd-kpis").html(kpis.map(x => `<div class="wafd-kpi"><span>${x[0]}</span><strong>${esc(x[1])}</strong></div>`).join(""));

    const alerts = d.alerts || {};
    const alertCards = [
      ["عجز المواد", alerts.material_shortages || 0, "WAFD Production Batch"],
      ["دفعات جودة مرفوضة", alerts.quality_rejected || 0, "WAFD Production Batch"],
      ["رحلات متأخرة", alerts.late_trips || 0, "WAFD Delivery Trip"],
      ["فواتير متأخرة", alerts.overdue_invoices || 0, "WAFD Invoice"],
      ["فواتير غير مسددة", alerts.unpaid_invoices || 0, "WAFD Invoice"],
      ["فجوة الإنتاج", alerts.production_gap || 0, "WAFD Production Batch"],
      ["تسليم دون إنتاج مسجل", alerts.delivery_without_production || 0, "WAFD Delivery Proof"]
    ];
    $root.find(".wafd-alerts").html(alertCards.map(x => `<button class="wafd-alert ${x[1] ? "has-alert" : ""}" data-route-doctype="${x[2]}"><span>${x[0]}</span><b>${x[1]}</b></button>`).join(""));

    const projects = d.projects || [];
    $root.find(".wafd-projects").html(projects.length ? `<table class="wafd-table"><thead><tr><th>المشروع</th><th>التقدم</th><th>المسلم</th><th>الربح</th></tr></thead><tbody>${projects.map(x => `<tr data-doctype="WAFD Catering Project" data-docname="${esc(x.name)}"><td>${esc(x.project_name || x.name)}</td><td>${flt(x.progress_percent || 0).toFixed(1)}%</td><td>${esc(x.delivered_meals || 0)} / ${esc(x.total_meals || 0)}</td><td>${money(x.profit)}</td></tr>`).join("")}</tbody></table>` : empty("لا توجد مشاريع"));

    const deliveries = d.upcoming_deliveries || [];
    $root.find(".wafd-deliveries").html(deliveries.length ? `<table class="wafd-table"><thead><tr><th>التاريخ</th><th>الفندق</th><th>الكمية</th><th>الحالة</th></tr></thead><tbody>${deliveries.map(x => `<tr data-doctype="WAFD Delivery Trip" data-docname="${esc(x.name)}"><td>${esc(x.trip_date)}</td><td>${esc(x.hotel)}</td><td>${esc(x.quantity)}</td><td>${status(x.status)}</td></tr>`).join("")}</tbody></table>` : empty("لا توجد توصيلات قادمة"));

    const invoices = d.overdue_invoices || [];
    $root.find(".wafd-invoices").html(invoices.length ? `<table class="wafd-table"><thead><tr><th>الفاتورة</th><th>الاستحقاق</th><th>الرصيد</th><th>الحالة</th></tr></thead><tbody>${invoices.map(x => `<tr data-doctype="WAFD Invoice" data-docname="${esc(x.name)}"><td>${esc(x.name)}</td><td>${esc(x.due_date)}</td><td>${money(x.balance)}</td><td>${status(x.status)}</td></tr>`).join("")}</tbody></table>` : empty("لا توجد فواتير متأخرة"));
  }

  load_dashboard();
};
