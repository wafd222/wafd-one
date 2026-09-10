frappe.pages["wafd-storekeeper-home"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("شاشة أمين المستودع"),
    single_column: true,
  });
  const $root = $(page.body).addClass("wafd-storekeeper-home").attr("dir", "rtl");

  const escape = (value) => frappe.utils.escape_html(String(value == null ? "" : value));
  let requestSerial = 0;

  function openMovement(type, extra = {}) {
    frappe.model.with_doctype("WAFD Stock Movement", () => {
      const doc = frappe.model.get_new_doc("WAFD Stock Movement");
      doc.movement_type = type;
      Object.assign(doc, extra);
      frappe.set_route("Form", "WAFD Stock Movement", doc.name);
    });
  }

  function renderShell() {
    $root.html(`
      <div class="wafd-storekeeper-wrap">
        <section class="wafd-storekeeper-head">
          <div><span>إدارة مبسطة للمستودع</span><h2>اختر العملية المطلوبة</h2></div>
          <button type="button" data-action="movements">سجل الحركات</button>
        </section>
        <section class="wafd-storekeeper-actions">
          <button class="is-primary" type="button" data-action="receipt"><b>＋</b><strong>استلام مواد مشتراة</strong><small>اختيار أمر الشراء والمستودع ثم تسجيل الكمية</small></button>
          <button type="button" data-action="issue"><b>−</b><strong>صرف مواد</strong><small>صرف الأصناف من المستودع إلى المستلم</small></button>
          <button type="button" data-action="transfer"><b>↔</b><strong>تحويل مواد</strong><small>نقل الأصناف بين مستودعين</small></button>
          <button type="button" data-action="orders"><b>⌑</b><strong>أوامر الشراء</strong><small>متابعة المواد المطلوب استلامها <i id="wafd-pending-orders"></i></small></button>
        </section>
        <section class="wafd-storekeeper-balances">
          <div class="wafd-storekeeper-balance-head"><div><span>أرصدة المخزون</span><small>الكميات الفعلية والمتاحة في المستودعات</small></div><button type="button" data-action="refresh">تحديث</button></div>
          <div class="wafd-storekeeper-filters">
            <select id="wafd-balance-warehouse"><option value="">كل المستودعات</option></select>
            <input id="wafd-balance-search" type="search" placeholder="ابحث باسم الصنف">
          </div>
          <div id="wafd-balance-results" class="wafd-storekeeper-results"><div class="wafd-storekeeper-loading">جارٍ تحميل الأرصدة…</div></div>
        </section>
      </div>`);

    $root.on("click", "[data-action='receipt']", () => openMovement("استلام / Receipt", { reference_type: "WAFD Purchase Order" }));
    $root.on("click", "[data-action='issue']", () => openMovement("صرف / Issue"));
    $root.on("click", "[data-action='transfer']", () => openMovement("تحويل / Transfer"));
    $root.on("click", "[data-action='orders']", () => frappe.set_route("List", "WAFD Purchase Order"));
    $root.on("click", "[data-action='movements']", () => frappe.set_route("List", "WAFD Stock Movement"));
    $root.on("click", "[data-action='refresh']", loadBalances);
    $root.on("change", "#wafd-balance-warehouse", loadBalances);
    let timer;
    $root.on("input", "#wafd-balance-search", () => {
      clearTimeout(timer);
      timer = setTimeout(loadBalances, 250);
    });
  }

  function renderBalances(data) {
    const warehouses = data.warehouses || [];
    const selected = $root.find("#wafd-balance-warehouse").val() || "";
    const $select = $root.find("#wafd-balance-warehouse");
    if ($select.find("option").length <= 1) {
      warehouses.forEach((row) => $select.append(`<option value="${escape(row.name)}">${escape(row.warehouse_name || row.name)}</option>`));
      $select.val(selected);
    }
    $root.find("#wafd-pending-orders").text(data.pending_purchase_orders ? `(${data.pending_purchase_orders})` : "");

    const rows = data.balances || [];
    if (!rows.length) {
      $root.find("#wafd-balance-results").html('<div class="wafd-storekeeper-empty">لا توجد أرصدة مطابقة.</div>');
      return;
    }
    $root.find("#wafd-balance-results").html(`
      <div class="wafd-storekeeper-table-head"><span>الصنف</span><span>المستودع</span><span>المتاح</span><span>المحجوز</span></div>
      ${rows.map((row) => `
        <div class="wafd-storekeeper-balance-row">
          <span data-label="الصنف"><b>${escape(row.ingredient)}</b><small>${escape(row.uom || "")}</small></span>
          <span data-label="المستودع">${escape(row.warehouse)}</span>
          <span data-label="المتاح" class="is-available">${escape(row.available_quantity || 0)}</span>
          <span data-label="المحجوز">${escape(row.reserved_quantity || 0)}</span>
        </div>`).join("")}`);
  }

  function loadBalances() {
    const serial = ++requestSerial;
    $root.find("#wafd-balance-results").addClass("is-loading");
    frappe.call({
      method: "wafd_one.storekeeper_portal.get_storekeeper_snapshot",
      args: {
        warehouse: $root.find("#wafd-balance-warehouse").val() || null,
        search: $root.find("#wafd-balance-search").val() || null,
      },
      callback(r) {
        if (serial !== requestSerial) return;
        $root.find("#wafd-balance-results").removeClass("is-loading");
        renderBalances(r.message || {});
      },
    });
  }

  renderShell();
  loadBalances();
};
