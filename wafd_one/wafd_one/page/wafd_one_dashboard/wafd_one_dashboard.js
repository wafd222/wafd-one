frappe.pages["wafd-one-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("WAFD ONE"),
    single_column: true,
  });

  const items = [
    ["المشاريع", "WAFD Catering Project", "octicon octicon-project"],
    ["البعثات والعملاء", "WAFD Mission", "octicon octicon-people"],
    ["الفنادق", "WAFD Hotel", "octicon octicon-home"],
    ["العقود", "WAFD Contract", "octicon octicon-file"],
    ["خطط الوجبات", "WAFD Meal Plan", "octicon octicon-checklist"],
    ["الوصفات", "WAFD Recipe", "octicon octicon-list-unordered"],
    ["مكونات الأغذية", "WAFD Ingredient", "octicon octicon-package"],
    ["دفعات الإنتاج", "WAFD Production Batch", "octicon octicon-gear"],
    ["فحص الجودة", "WAFD Quality Inspection", "octicon octicon-shield"],
    ["التغليف", "WAFD Packaging Record", "octicon octicon-package"],
    ["رحلات التوصيل", "WAFD Delivery Trip", "octicon octicon-location"],
    ["إثبات التسليم", "WAFD Delivery Proof", "octicon octicon-device-camera"],
    ["المستودعات", "WAFD Warehouse", "octicon octicon-archive"],
    ["حركة المخزون", "WAFD Stock Movement", "octicon octicon-sync"],
    ["الموردون", "WAFD Supplier", "octicon octicon-briefcase"],
    ["أوامر الشراء", "WAFD Purchase Order", "octicon octicon-cart"],
    ["المركبات", "WAFD Vehicle", "octicon octicon-truck"],
    ["السائقون", "WAFD Driver", "octicon octicon-person"],
    ["تكاليف المشاريع", "WAFD Project Cost", "octicon octicon-graph"],
    ["إيرادات المشاريع", "WAFD Project Revenue", "octicon octicon-credit-card"],
    ["الفواتير", "WAFD Invoice", "octicon octicon-file-text"],
    ["التحصيلات", "WAFD Payment", "octicon octicon-check"],
  ];

  const $root = $(wrapper).find(".layout-main-section");
  $root.attr("dir", "rtl").html(`
    <div class="wafd-dashboard">
      <div class="wafd-hero">
        <div>
          <h2>WAFD ONE</h2>
          <p>منصة موحدة لإدارة مشاريع الإعاشة والتخطيط والإنتاج والجودة والتوزيع والمخزون والمالية.</p>
        </div>
      </div>
      <div class="wafd-section-title">مؤشرات اليوم</div><div class="wafd-kpis"></div><div class="wafd-section-title">العمليات الرئيسية</div>
      <div class="wafd-grid"></div>
    </div>
  `);

  const $grid = $root.find(".wafd-grid");
  items.forEach(([label, doctype, icon]) => {
    const $card = $(`
      <button type="button" class="wafd-card" data-doctype="${frappe.utils.escape_html(doctype)}">
        <span class="wafd-card-icon ${icon}"></span>
        <span class="wafd-card-label">${frappe.utils.escape_html(label)}</span>
        <span class="wafd-card-arrow">‹</span>
      </button>
    `);
    $grid.append($card);
  });

  $root.on("click", ".wafd-card", function () {
    frappe.set_route("List", $(this).data("doctype"));
  });

  frappe.call({method:"wafd_one.finance.get_dashboard_data"}).then(r=>{const d=r.message||{};const fmt=v=>format_currency(v||0,"SAR");const cards=[["المشاريع النشطة",d.active_projects],["وجبات اليوم",d.planned_meals_today],["المسلم اليوم",d.delivered_meals_today],["المستحقات",fmt(d.receivables)],["الإيراد المحصل",fmt(d.collected_revenue)],["الربح",fmt(d.profit)]];const root=$(wrapper).find(".wafd-kpis");cards.forEach(x=>root.append(`<div class="wafd-kpi"><span>${frappe.utils.escape_html(String(x[0]))}</span><strong>${frappe.utils.escape_html(String(x[1]))}</strong></div>`));});
};

