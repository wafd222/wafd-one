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

      <section class="wafd-section-head wafd-hub-section-head"><div><span>أقسام النظام</span><small>الوصول إلى التفاصيل عند الحاجة دون ازدحام الواجهة الرئيسية</small></div></section>
      <section class="wafd-hub-grid">
        <button class="wafd-hub-card" data-route="wafd-operations-hub"><b>⚙</b><span>التشغيل</span><small>المشاريع والخطط والإنتاج والجودة والتغليف</small></button>
        <button class="wafd-hub-card" data-route="wafd-inventory-hub"><b>▣</b><span>المخزون والمشتريات</span><small>المواد والمستودعات والثلاجات والحركات والمشتريات</small></button>
        <button class="wafd-hub-card" data-route="wafd-delivery-hub"><b>➜</b><span>التوصيل</span><small>التحميل والرحلات والتسليم والاستلام</small></button>
        <button class="wafd-hub-card" data-route="wafd-finance-hub"><b>ر.س</b><span>المالية</span><small>الفواتير والتحصيل والمراجعة المالية</small></button>
        <button class="wafd-hub-card" data-route="wafd-master-data-hub"><b>◆</b><span>البيانات المرجعية</span><small>الفنادق والوصفات والمواد والبيانات الأساسية</small></button>
        <button class="wafd-hub-card" data-route="wafd-documents-hub"><b>▤</b><span>المستندات والتعهدات</span><small>التعهدات والمستندات والطباعة</small></button>
      </section>

      <section class="wafd-control-strip">
        <div class="wafd-control-title"><span>الفترة التشغيلية</span><small>تحديث المؤشرات والمشاريع حسب التاريخ</small></div>
        <label>من<input type="date" class="form-control wafd-from"></label>
        <label>إلى<input type="date" class="form-control wafd-to"></label>
        <button class="wafd-refresh">تحديث البيانات</button>
      </section>

      <section class="wafd-section-head"><div><span>مسار التشغيل المتكامل</span><small>افتح أي مرحلة مباشرة</small></div></section>
      <section class="wafd-flow-pro"></section>

      <section class="wafd-section-head"><div><span>ملخص الإدارة</span><small>صورة شاملة عن التشغيل والمالية والمخزون</small></div></section>
      <section class="wafd-kpi-grid wafd-kpi-grid-wide"></section>

      <section class="wafd-manager-overview">
        <article class="wafd-card wafd-overview-card">
          <div class="wafd-card-head"><div><h3>ملخص اليوم</h3><small>التخطيط والإنتاج والتوصيل</small></div></div>
          <div class="wafd-today-ops"></div>
        </article>
        <article class="wafd-card wafd-overview-card">
          <div class="wafd-card-head"><div><h3>الوضع المالي</h3><small>الفوترة والتحصيل والربحية</small></div></div>
          <div class="wafd-finance-summary"></div>
        </article>
        <article class="wafd-card wafd-overview-card">
          <div class="wafd-card-head"><div><h3>حالة المخزون</h3><small>القيمة والعجز والمستودعات</small></div></div>
          <div class="wafd-inventory-summary"></div>
        </article>
      </section>

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
  $root.on("click", "[data-low-stock]", function () { showLowStock($(this).data("warehouse") || ""); });
  $root.on("click", ".wafd-refresh", load);
  $root.on("click", ".wafd-refresh-alerts", function () {
    frappe.call({
      method: "wafd_one.executive.refresh_executive_alerts",
      freeze: true,
      freeze_message: __("جارٍ تحديث التنبيهات الإدارية...")
    }).then(() => {
      frappe.show_alert({ message: __("تم تحديث التنبيهات"), indicator: "green" });
      load();
    }).catch(() => {
      frappe.msgprint(__("تعذر تحديث التنبيهات الإدارية. راجع الصلاحيات أو سجل الأخطاء."));
    });
  });

  function escape(value) { return frappe.utils.escape_html(String(value ?? "")); }
  function toFloat(value) { const number = Number.parseFloat(value); return Number.isFinite(number) ? number : 0; }
  function toInt(value) { const number = Number.parseInt(value, 10); return Number.isFinite(number) ? number : 0; }
  function money(value) { return format_currency(toFloat(value), "SAR"); }
  function empty(message) { return `<div class="wafd-empty">${escape(message)}</div>`; }

  function showLowStock(warehouse) {
    frappe.call({
      method: "wafd_one.executive.get_low_stock_details",
      args: { warehouse: warehouse || null },
      freeze: true,
      freeze_message: __("جارٍ تحميل كميات المخزون...")
    }).then((response) => {
      const rows = response.message || [];
      const title = warehouse ? `المخزون المنخفض — ${warehouse}` : "الأصناف المنخفضة أو النافدة";
      const html = rows.length ? `<div class="wafd-low-stock-dialog"><table class="table table-bordered"><thead><tr><th>الصنف</th><th>المتاح</th><th>الحد الأدنى</th><th>الوحدة</th><th>المستودع</th></tr></thead><tbody>${rows.map(row => `<tr data-balance="${escape(row.name)}"><td><b>${escape(row.ingredient)}</b></td><td class="${toFloat(row.available_quantity) <= 0 ? 'text-danger' : ''}">${escape(row.available_quantity || 0)}</td><td>${escape(row.minimum_stock || 0)}</td><td>${escape(row.uom || '')}</td><td>${escape(row.warehouse || '')}</td></tr>`).join("")}</tbody></table></div>` : empty("لا توجد أصناف منخفضة في هذا المستودع.");
      const dialog = new frappe.ui.Dialog({ title, size: "extra-large", fields: [{ fieldtype: "HTML", fieldname: "stock_html" }] });
      dialog.fields_dict.stock_html.$wrapper.html(html);
      dialog.$wrapper.on("click", "[data-balance]", function () {
        frappe.set_route("Form", "WAFD Stock Balance", $(this).data("balance"));
        dialog.hide();
      });
      dialog.show();
    }).catch(() => frappe.msgprint(__("تعذر تحميل تفاصيل المخزون المنخفض.")));
  }

  function load() {
    frappe.call({
      method: "wafd_one.executive.get_executive_dashboard_data",
      args: { from_date: $root.find(".wafd-from").val(), to_date: $root.find(".wafd-to").val() },
      freeze: true,
      freeze_message: __("جارٍ تحديث مركز العمليات...")
    }).then((response) => render(response.message || {})).catch(() => {
      frappe.msgprint(__("تعذر تحميل لوحة المدير. أعد المحاولة أو راجع سجل الأخطاء."));
    });
  }

  function render(data) {
    const marginBase = toFloat(data.recognized_revenue || data.invoiced_revenue || 0);
    const margin = marginBase ? (toFloat(data.profit || 0) / marginBase * 100) : 0;
    const kpis = [
      ["العقود النشطة", data.executive_risks?.expiring_contracts != null ? (data.active_contracts || 0) : 0, "عقود", "WAFD Contract"],
      ["المشاريع الجارية", data.active_projects || 0, "تشغيل", "WAFD Catering Project"],
      ["وجبات مخططة", data.planned_meals || 0, "تخطيط", "WAFD Daily Meal Plan"],
      ["وجبات مسلّمة", data.delivered_meals || 0, "توصيل", "WAFD Delivery Proof"],
      ["قيمة الفواتير شامل الضريبة", money(data.invoiced_revenue), "فواتير", "WAFD Invoice"],
      ["المحصّل شامل الضريبة", money(data.collected_revenue), "تحصيل", "WAFD Payment"],
      ["المستحق", money(data.receivables), "ذمم", "WAFD Invoice"],
      ["هامش الربح", `${margin.toFixed(1)}%`, "ربحية", "WAFD Catering Project"]
    ];
    $root.find(".wafd-kpi-grid").html(kpis.map((item) => `
      <button data-list="${item[3]}"><small>${item[2]}</small><span>${item[0]}</span><strong>${escape(item[1])}</strong><i>عرض التفاصيل ←</i></button>
    `).join(""));


    const todayOps = data.today_operations || {};
    $root.find(".wafd-today-ops").html([
      ["خطط اليوم", todayOps.planned || 0], ["دفعات الإنتاج", todayOps.production || 0],
      ["رحلات اليوم", todayOps.trips || 0], ["تم التسليم", todayOps.delivered || 0]
    ].map(x => `<div><strong>${escape(x[1])}</strong><span>${x[0]}</span></div>`).join(""));

    $root.find(".wafd-finance-summary").html(`
      <div><span>الإيراد المفوتر قبل الضريبة</span><strong>${money(data.recognized_revenue || 0)}</strong></div>
      <div><span>ضريبة الفواتير</span><strong>${money(data.invoiced_vat || 0)}</strong></div>
      <div><span>المحصّل شامل الضريبة</span><strong>${money(data.collected_revenue)}</strong></div>
      <div><span>صافي المحصّل قبل الضريبة</span><strong>${money(data.net_collected_revenue || 0)}</strong></div>
      <div><span>ضريبة محصّلة</span><strong>${money(data.collected_vat || 0)}</strong></div>
      <div><span>التكلفة الفعلية</span><strong>${money(data.actual_cost)}</strong></div>
      <div><span>الربح التشغيلي بعد استبعاد الضريبة</span><strong class="${toFloat(data.profit)<0?'is-negative':''}">${money(data.profit)}</strong></div>
      <div><span>المتأخر</span><strong>${money(data.overdue_receivables)}</strong></div>`);

    const inv = data.inventory_snapshot || {};
    $root.find(".wafd-inventory-summary").html(`
      <div><span>قيمة المخزون</span><strong>${money(inv.total_value)}</strong></div>
      <div><span>أصناف منخفضة أو نافدة</span><strong class="${toInt(inv.low_items)?'is-negative':''}">${escape(inv.low_items || 0)}</strong></div>
      <div><span>معدل التسليم</span><strong>${toFloat(data.delivery_rate || 0).toFixed(1)}%</strong></div>
      <div><span>الوجبات المرفوضة</span><strong>${escape(data.rejected_meals || 0)}</strong></div>`);

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
      <tr data-doctype="WAFD Catering Project" data-docname="${escape(row.name)}"><td><b>${escape(row.project_name || row.name)}</b><small>${escape(row.name)}</small></td><td><div class="wafd-progress"><i style="width:${Math.min(100, toFloat(row.progress_percent || 0))}%"></i></div><span>${toFloat(row.progress_percent || 0).toFixed(0)}%</span></td><td>${escape(row.delivered_meals || 0)} / ${escape(row.total_meals || 0)}</td></tr>
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
      <tr data-doctype="WAFD Catering Project" data-docname="${escape(row.name)}"><td><b>${escape(row.project_name || row.name)}</b><small>${escape(row.primary_hotel || "")}</small></td><td>${money(row.profit)}</td><td>${toFloat(row.profit_margin_percent || 0).toFixed(1)}%</td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد بيانات ربحية كافية بعد."));

    const drivers = data.driver_performance || [];
    $root.find(".wafd-driver-performance").html(drivers.length ? `<table><thead><tr><th>السائق</th><th>الرحلات</th><th>في الوقت</th><th>متأخرة</th></tr></thead><tbody>${drivers.slice(0, 6).map((row) => `
      <tr><td><b>${escape(row.driver)}</b></td><td>${escape(row.trips || 0)}</td><td>${escape(row.on_time_trips || 0)}</td><td>${escape(row.delayed_trips || 0)}</td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد بيانات توصيل كافية بعد."));

    const consumed = (data.inventory_snapshot || {}).top_consumed || [];
    $root.find(".wafd-top-consumed").html(consumed.length ? `<table><thead><tr><th>الصنف</th><th>الكمية المصروفة</th><th>الوحدة</th><th>الحركات</th></tr></thead><tbody>${consumed.map(row => `<tr><td><b>${escape(row.ingredient)}</b></td><td>${escape(row.quantity || 0)}</td><td>${escape(row.uom || '')}</td><td>${escape(row.movement_count || 0)}</td></tr>`).join("")}</tbody></table>` : empty("لا توجد حركات صرف مرحلة بعد."));

    const warehouses = (data.inventory_snapshot || {}).warehouses || [];
    $root.find(".wafd-warehouse-status").html(warehouses.length ? `<table><thead><tr><th>المستودع</th><th>الكمية المتاحة</th><th>قيمة المخزون</th><th>منخفض</th></tr></thead><tbody>${warehouses.map(row => `<tr><td><b>${escape(row.warehouse)}</b><small>${escape(row.item_count || 0)} صنف</small></td><td><small>${escape(row.quantity_summary || "0")}</small></td><td>${money(row.stock_value)}</td><td><button type="button" class="wafd-status-pill wafd-low-stock-button ${toInt(row.low_items)?'is-warn':''}" data-low-stock="1" data-warehouse="${escape(row.warehouse)}" title="عرض كميات الأصناف المنخفضة">${escape(row.low_items || 0)}</button></td></tr>`).join("")}</tbody></table>` : empty("لا توجد أرصدة مخزون بعد."));


    const cabinets = data.hot_cabinets || {};
    const cabinetRows = cabinets.rows || [];
    $root.find(".wafd-hot-cabinet-status").html(cabinetRows.length ? `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px"><span class="wafd-status-pill">الإجمالي: ${escape(cabinets.total || 0)}</span><span class="wafd-status-pill">متاح: ${escape(cabinets.available || 0)}</span><span class="wafd-status-pill is-warn">لدى الفنادق: ${escape(cabinets.at_hotels || 0)}</span><span class="wafd-status-pill">السفندشات: ${escape(cabinets.sandwiches || 0)}</span></div><table><thead><tr><th>السخان</th><th>الفندق</th><th>السفندشات</th><th>الحالة</th></tr></thead><tbody>${cabinetRows.filter(r => r.current_hotel || toInt(r.current_sandwich_count)).slice(0,10).map(r => `<tr data-doctype="WAFD Hot Cabinet" data-docname="${escape(r.name)}"><td><b>${escape(r.sequence_number || r.name)}</b></td><td>${escape(r.current_hotel || "—")}</td><td>${escape(r.current_sandwich_count || 0)}</td><td>${escape(r.status || "")}</td></tr>`).join("")}</tbody></table>` : empty("لم يتم تسجيل السخانات بعد."));

    const hotels = data.hotel_performance || [];
    $root.find(".wafd-hotel-performance").html(hotels.length ? `<table><thead><tr><th>الفندق</th><th>التسليمات</th><th>المقبول</th><th>نسبة القبول</th></tr></thead><tbody>${hotels.slice(0, 6).map((row) => `
      <tr><td><b>${escape(row.hotel)}</b></td><td>${escape(row.deliveries || 0)}</td><td>${escape(row.accepted_quantity || 0)}</td><td>${toFloat(row.acceptance_percent || 0).toFixed(1)}%</td></tr>
    `).join("")}</tbody></table>` : empty("لا توجد بيانات استلام كافية بعد."));
  }

  load();
};
