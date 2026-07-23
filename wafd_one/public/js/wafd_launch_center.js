frappe.pages["wafd-launch-center"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("مركز الجاهزية"), single_column: true });
  const $main = $(wrapper).find(".layout-main-section").attr("dir", "rtl");

  $main.html(`
    <div class="wafd-launch wafd-launch-final">
      <div class="launch-hero">
        <div><small>النسخة المرشحة للتجربة</small><h1>مركز جاهزية WAFD ONE</h1><p>فحص مختصر للبيانات الأساسية قبل بدء التجربة التشغيلية.</p></div>
        <div class="launch-hero-buttons"><button class="btn btn-light" data-route="wafd-one-dashboard">لوحة التشغيل</button><button class="btn btn-light refresh-ready">إعادة الفحص</button></div>
      </div>
      <div class="launch-status"></div>
      <div class="launch-counts"></div>
      <div class="launch-title">خطوات التجربة</div>
      <div class="launch-flow"></div>
    </div>`);

  const flow = [
    ["1", "العقد", "WAFD Contract"], ["2", "المشروع", "WAFD Catering Project"],
    ["3", "الخطة اليومية", "WAFD Daily Meal Plan"], ["4", "الإنتاج", "WAFD Production Batch"],
    ["5", "الجودة والتغليف", "WAFD Quality Inspection"], ["6", "التوصيل", "WAFD Delivery Trip"],
    ["7", "الفاتورة والتحصيل", "WAFD Invoice"],
  ];
  $main.find(".launch-flow").html(flow.map((item) => `<button data-list="${item[2]}"><b>${item[0]}</b><span>${item[1]}</span></button>`).join(""));

  $main.on("click", "[data-route]", function () { frappe.set_route($(this).data("route")); });
  $main.on("click", "[data-list]", function () { frappe.set_route("List", $(this).data("list")); });
  $main.on("click", ".refresh-ready", load);

  function load() {
    frappe.call({ method: "wafd_one.readiness.get_release_readiness", freeze: true }).then((response) => {
      const data = response.message || {};
      const checks = data.checks || [];
      $main.find(".launch-status").html(`
        <div class="ready-head ${data.ready ? "ok" : "warn"}"><strong>${data.ready ? "البيانات الأساسية جاهزة للتجربة" : "توجد ملاحظات يجب استكمالها"}</strong><span>${data.version || ""}</span></div>
        <div class="ready-list">${checks.map((row) => `<div class="ready-row"><i class="${row.ok ? "ok" : "bad"}">${row.ok ? "✓" : "!"}</i><div><b>${frappe.utils.escape_html(row.label || "")}</b><small>${frappe.utils.escape_html(row.detail || "")}</small></div></div>`).join("")}</div>`);
      const counts = data.counts || {};
      const cards = { العقود: counts.contracts || 0, المشاريع: counts.projects || 0, "الخطط اليومية": counts.daily_plans || 0, "دفعات الإنتاج": counts.production_batches || 0, التسليمات: counts.deliveries || 0, الفواتير: counts.invoices || 0 };
      $main.find(".launch-counts").html(Object.entries(cards).map((item) => `<div><span>${item[0]}</span><b>${item[1]}</b></div>`).join(""));
    });
  }
  load();
};
