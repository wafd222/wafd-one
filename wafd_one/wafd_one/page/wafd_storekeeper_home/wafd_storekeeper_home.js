frappe.pages["wafd-storekeeper-home"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({parent: wrapper, title: __("شاشة أمين المستودع"), single_column: true});
  const $root = $(page.body).addClass("wafd-storekeeper-home").attr("dir", "rtl");
  const esc = (value) => frappe.utils.escape_html(String(value == null ? "" : value));
  let snapshotSerial = 0;

  const api = (method, args = {}, options = {}) => frappe.call({
    method: `wafd_one.storekeeper_portal.${method}`,
    args,
    freeze: Boolean(options.freeze),
    freeze_message: options.message,
  });
  const warehouseLabel = (row) => `${row.warehouse_name || row.name} — ${row.warehouse_type || ""}`;
  const optionsHtml = (rows, valueKey, labelFn, placeholder) =>
    `<option value="">${esc(placeholder)}</option>${rows.map((row) => `<option value="${esc(row[valueKey])}">${esc(labelFn(row))}</option>`).join("")}`;

  function readSelected($box, selected, mode) {
    $box.find(".wafd-material-card").each(function () {
      const $row = $(this);
      const ingredient = String($row.data("ingredient") || "");
      if (!$row.find(".wafd-material-check").prop("checked")) {
        selected.delete(ingredient);
        return;
      }
      selected.set(ingredient, {
        ingredient,
        quantity: Number($row.find(".wafd-material-qty").val() || 0),
        unit_cost: Number($row.find(".wafd-material-price").val() || 0),
        expiry_date: mode === "receipt" ? ($row.find(".wafd-material-expiry").val() || null) : null,
      });
    });
  }

  function renderMaterialCards($box, rows, selected, mode) {
    if (!rows.length) {
      $box.html('<div class="wafd-storekeeper-empty">لا توجد مواد مطابقة. جرّب قسماً آخر أو كلمة بحث مختلفة.</div>');
      return;
    }
    $box.html(rows.map((item) => {
      const saved = selected.get(item.ingredient) || {};
      const available = Number(item.available_quantity || 0);
      return `<div class="wafd-material-card ${saved.ingredient ? "is-selected" : ""}" data-ingredient="${esc(item.ingredient)}">
        <input class="wafd-material-check" type="checkbox" ${saved.ingredient ? "checked" : ""}>
        <div class="wafd-material-name"><strong>${esc(item.ingredient)}</strong><small>${esc(item.category || "بدون قسم")} · ${esc(item.uom || "")}${mode === "handover" ? ` · المتاح ${esc(available)}` : ""}</small></div>
        <label><span>الكمية</span><input class="wafd-material-qty" type="number" inputmode="decimal" min="0" ${mode === "handover" ? `max="${esc(available)}"` : ""} step="any" value="${esc(saved.quantity || "")}" placeholder="0"></label>
        <label><span>سعر الوحدة</span><input class="wafd-material-price" type="number" inputmode="decimal" min="0" step="any" value="${esc(saved.unit_cost == null ? item.unit_cost || 0 : saved.unit_cost)}"></label>
        ${mode === "receipt" ? `<label class="wafd-expiry-field"><span>تاريخ الانتهاء (اختياري)</span><input class="wafd-material-expiry" type="date" value="${esc(saved.expiry_date || "")}"></label>` : ""}
      </div>`;
    }).join(""));
    $box.off("click.wafdPicker change.wafdPicker")
      .on("click.wafdPicker", ".wafd-material-card", function (event) {
        if ($(event.target).is("input,label,span")) return;
        const $check = $(this).find(".wafd-material-check");
        $check.prop("checked", !$check.prop("checked")).trigger("change");
      })
      .on("change.wafdPicker", ".wafd-material-check", function () {
        $(this).closest(".wafd-material-card").toggleClass("is-selected", this.checked);
      });
  }

  async function openReceipt() {
    const base = (await api("get_storekeeper_workflow_options", {receipt: 1}, {freeze: true})).message || {};
    if (!(base.warehouses || []).length) return frappe.msgprint(__("لا يوجد مستودع أو ثلاجة نشطة."));
    const selected = new Map();
    let searchTimer;
    const dialog = new frappe.ui.Dialog({
      title: __("استلام وتوزيع المشتريات"), size: "large",
      fields: [{fieldname: "guided_receipt", fieldtype: "HTML"}],
      primary_action_label: __("إضافة المواد للمخزون"),
      primary_action: async () => {
        const $panel = dialog.fields_dict.guided_receipt.$wrapper;
        readSelected($panel.find("#wafd-receipt-items"), selected, "receipt");
        const target = $panel.find("#wafd-receipt-warehouse").val();
        const rows = [...selected.values()].filter((row) => row.quantity > 0);
        if (!target) return frappe.msgprint(__("اختر المستودع أو الثلاجة التي ستوضع فيها المواد."));
        if (!rows.length) return frappe.msgprint(__("اختر مادة واحدة على الأقل واكتب الكمية."));
        const result = await api("receive_inventory_materials", {target_warehouse: target, items: JSON.stringify(rows)}, {freeze: true, message: __("جارٍ إضافة المواد وتحديث المخزون…")});
        if (!result.message) return;
        dialog.hide();
        frappe.show_alert({message: __(`تمت إضافة ${result.message.items_count} مادة إلى ${result.message.warehouse}`), indicator: "green"}, 6);
        loadSnapshot();
      },
    });
    dialog.show();
    const $panel = dialog.fields_dict.guided_receipt.$wrapper;
    $panel.html(`<div class="wafd-guided-panel">
      <div class="wafd-step"><b>1</b><div><strong>أين ستوضع المواد؟</strong><small>اختر المستودع أو الثلاجة مباشرة ويمكن تغييره دون مسح النص.</small></div></div>
      <select id="wafd-receipt-warehouse">${optionsHtml(base.warehouses || [], "name", warehouseLabel, "اختر المستودع أو الثلاجة")}</select>
      <div class="wafd-step"><b>2</b><div><strong>ابحث ثم اختر المواد</strong><small>اختر القسم أو اكتب اسم المادة، ثم اضغط البطاقة وأدخل الكمية والسعر.</small></div></div>
      <div class="wafd-picker-filters"><select id="wafd-receipt-category">${optionsHtml((base.categories || []).map((category) => ({category})), "category", (row) => row.category, "كل الأقسام")}</select><input id="wafd-receipt-search" type="search" placeholder="ابحث باسم المادة أو رمزها"></div>
      <div id="wafd-receipt-items" class="wafd-material-results"><div class="wafd-picker-help">اختر قسماً أو اكتب حرفين على الأقل لعرض المواد.</div></div>
      <button type="button" class="wafd-secondary-link" id="wafd-open-orders">عرض أوامر الشراء</button>
    </div>`);
    const load = async () => {
      const category = $panel.find("#wafd-receipt-category").val();
      const search = $panel.find("#wafd-receipt-search").val().trim();
      const $box = $panel.find("#wafd-receipt-items");
      readSelected($box, selected, "receipt");
      if (!category && search.length < 2) return $box.html('<div class="wafd-picker-help">اختر قسماً أو اكتب حرفين على الأقل لعرض المواد.</div>');
      $box.html('<div class="wafd-storekeeper-loading">جارٍ البحث…</div>');
      const response = await api("get_storekeeper_workflow_options", {warehouse: $panel.find("#wafd-receipt-warehouse").val() || null, category: category || null, search: search || null, receipt: 1});
      renderMaterialCards($box, (response.message || {}).items || [], selected, "receipt");
    };
    $panel.on("change", "#wafd-receipt-category", load);
    $panel.on("change", "#wafd-receipt-warehouse", () => { selected.clear(); load(); });
    $panel.on("input", "#wafd-receipt-search", () => { clearTimeout(searchTimer); searchTimer = setTimeout(load, 250); });
    $panel.on("click", "#wafd-open-orders", () => frappe.set_route("List", "WAFD Purchase Order"));
  }

  async function openHandover() {
    const base = (await api("get_storekeeper_workflow_options", {}, {freeze: true})).message || {};
    if (!(base.warehouses || []).length) return frappe.msgprint(__("لا يوجد مستودع أو ثلاجة نشطة."));
    if (!(base.recipients || []).length) return frappe.msgprint(__("لا يوجد موظفون نشطون في الوظائف المسموح التسليم لها."));
    const selected = new Map();
    const roles = [...new Map((base.recipients || []).map((row) => [row.role, row.role_label])).entries()].map(([role, label]) => ({role, label}));
    let searchTimer;
    const dialog = new frappe.ui.Dialog({
      title: __("تسليم مواد للموظفين"), size: "large",
      fields: [{fieldname: "guided_handover", fieldtype: "HTML"}],
      primary_action_label: __("تسليم وتحديث الرصيد"),
      primary_action: async () => {
        const $panel = dialog.fields_dict.guided_handover.$wrapper;
        readSelected($panel.find("#wafd-handover-items"), selected, "handover");
        const role = $panel.find("#wafd-recipient-role").val();
        const recipient = $panel.find("#wafd-recipient-name").val();
        const source = $panel.find("#wafd-source-warehouse").val();
        const rows = [...selected.values()].filter((row) => row.quantity > 0);
        if (!role || !recipient) return frappe.msgprint(__("اختر وظيفة المستلم ثم اسمه."));
        if (!source) return frappe.msgprint(__("اختر المستودع أو الثلاجة المصدر."));
        if (!rows.length) return frappe.msgprint(__("اختر مادة واحدة على الأقل واكتب الكمية."));
        const result = await api("create_employee_handover", {source_warehouse: source, issued_to_user: recipient, recipient_role: role, items: JSON.stringify(rows)}, {freeze: true, message: __("جارٍ تسليم المواد وتحديث الرصيد…")});
        if (!result.message) return;
        dialog.hide();
        frappe.show_alert({message: __(`تم تسليم المواد إلى ${result.message.recipient}`), indicator: "green"}, 6);
        loadSnapshot();
      },
    });
    dialog.show();
    const $panel = dialog.fields_dict.guided_handover.$wrapper;
    $panel.html(`<div class="wafd-guided-panel">
      <div class="wafd-step"><b>1</b><div><strong>من هو المستلم؟</strong><small>اختر الوظيفة أولاً ثم يظهر اسم الموظف، وليس البريد الإلكتروني.</small></div></div>
      <div class="wafd-picker-filters"><select id="wafd-recipient-role">${optionsHtml(roles, "role", (row) => row.label, "اختر الوظيفة")}</select><select id="wafd-recipient-name"><option value="">اختر اسم المستلم</option></select></div>
      <div class="wafd-step"><b>2</b><div><strong>من أين ستخرج المواد؟</strong><small>اختر المستودع أو الثلاجة المصدر.</small></div></div>
      <select id="wafd-source-warehouse">${optionsHtml(base.warehouses || [], "name", warehouseLabel, "اختر المستودع أو الثلاجة")}</select>
      <div class="wafd-step"><b>3</b><div><strong>اختر المواد</strong><small>اختر القسم أو ابحث، ولن تظهر إلا المواد ذات الرصيد المتاح.</small></div></div>
      <div class="wafd-picker-filters"><select id="wafd-handover-category">${optionsHtml((base.categories || []).map((category) => ({category})), "category", (row) => row.category, "كل الأقسام")}</select><input id="wafd-handover-search" type="search" placeholder="ابحث باسم المادة أو رمزها"></div>
      <div id="wafd-handover-items" class="wafd-material-results"><div class="wafd-picker-help">اختر المستودع ثم القسم، أو اكتب حرفين للبحث.</div></div>
    </div>`);
    const updateNames = () => {
      const role = $panel.find("#wafd-recipient-role").val();
      const people = (base.recipients || []).filter((row) => row.role === role);
      $panel.find("#wafd-recipient-name").html(optionsHtml(people, "name", (row) => row.full_name, "اختر اسم المستلم"));
    };
    const load = async () => {
      const warehouse = $panel.find("#wafd-source-warehouse").val();
      const category = $panel.find("#wafd-handover-category").val();
      const search = $panel.find("#wafd-handover-search").val().trim();
      const $box = $panel.find("#wafd-handover-items");
      readSelected($box, selected, "handover");
      if (!warehouse || (!category && search.length < 2)) return $box.html('<div class="wafd-picker-help">اختر المستودع ثم القسم، أو اكتب حرفين للبحث.</div>');
      $box.html('<div class="wafd-storekeeper-loading">جارٍ البحث في الرصيد المتاح…</div>');
      const response = await api("get_storekeeper_workflow_options", {warehouse, category: category || null, search: search || null});
      renderMaterialCards($box, (response.message || {}).items || [], selected, "handover");
    };
    $panel.on("change", "#wafd-recipient-role", updateNames);
    $panel.on("change", "#wafd-handover-category", load);
    $panel.on("change", "#wafd-source-warehouse", () => { selected.clear(); load(); });
    $panel.on("input", "#wafd-handover-search", () => { clearTimeout(searchTimer); searchTimer = setTimeout(load, 250); });
  }

  function renderShell() {
    $root.html(`<div class="wafd-storekeeper-wrap">
      <section class="wafd-storekeeper-head"><div><span>إدارة عملية بدون نماذج معقدة</span><h2>ماذا تريد أن تعمل الآن؟</h2></div><button type="button" data-action="movements">سجل الحركات</button></section>
      <section class="wafd-storekeeper-actions wafd-three-actions">
        <button class="is-primary" type="button" data-action="receive"><b>＋</b><strong>استلام وتوزيع المشتريات</strong><small>اختر المستودع أو الثلاجة، ثم ابحث عن المواد وسجّل الكمية والسعر.</small></button>
        <button type="button" data-action="handover"><b>➜</b><strong>تسليم مواد للموظفين</strong><small>مشرف النظافة أو مشرف الطبخ والشيف وغيرهم، بالاسم والوظيفة.</small></button>
        <button type="button" data-action="inventory"><b>▣</b><strong>معلومات المخزون</strong><small>كل الأرصدة والمواد الناقصة والمنتهية أو القريبة من الانتهاء.</small></button>
      </section>
      <section id="wafd-inventory-panel" class="wafd-storekeeper-balances" hidden>
        <div class="wafd-storekeeper-balance-head"><div><span>معلومات المخزون</span><small>بحث وفلاتر وتنبيهات عملية</small></div><button type="button" data-action="refresh">تحديث</button></div>
        <div id="wafd-inventory-summary" class="wafd-inventory-summary"></div>
        <div class="wafd-storekeeper-filters"><select id="wafd-balance-warehouse"><option value="">كل المستودعات والثلاجات</option></select><input id="wafd-balance-search" type="search" placeholder="ابحث باسم المادة أو المستودع"></div>
        <div class="wafd-inventory-tabs"><button class="is-active" data-view="all">كل المواد</button><button data-view="low">الناقص والصفر</button><button data-view="expiry">قريب الانتهاء</button></div>
        <div id="wafd-balance-results" class="wafd-storekeeper-results"><div class="wafd-storekeeper-loading">جارٍ تحميل معلومات المخزون…</div></div>
      </section>
    </div>`);
    $root.on("click", "[data-action='receive']", openReceipt);
    $root.on("click", "[data-action='handover']", openHandover);
    $root.on("click", "[data-action='inventory']", showInventory);
    $root.on("click", "[data-action='movements']", () => frappe.set_route("List", "WAFD Stock Movement"));
    $root.on("click", "[data-action='refresh']", loadSnapshot);
    $root.on("change", "#wafd-balance-warehouse", loadSnapshot);
    let timer;
    $root.on("input", "#wafd-balance-search", () => { clearTimeout(timer); timer = setTimeout(loadSnapshot, 250); });
    $root.on("click", ".wafd-inventory-tabs button", function () {
      $root.find(".wafd-inventory-tabs button").removeClass("is-active");
      $(this).addClass("is-active");
      renderInventory($root.data("snapshot") || {});
    });
  }

  function showInventory() {
    const panel = $root.find("#wafd-inventory-panel").prop("hidden", false)[0];
    panel?.scrollIntoView({behavior: "smooth", block: "start"});
    loadSnapshot();
  }

  function renderInventory(data) {
    $root.data("snapshot", data);
    const summary = data.summary || {};
    $root.find("#wafd-inventory-summary").html([
      [summary.materials || 0, "أرصدة مسجلة"], [summary.low || 0, "تحت الحد الأدنى"],
      [summary.zero || 0, "رصيدها صفر"], [(summary.expiring || 0) + (summary.expired || 0), "تنبيه انتهاء"],
    ].map(([value, label]) => `<div><b>${esc(value)}</b><small>${label}</small></div>`).join(""));
    const $select = $root.find("#wafd-balance-warehouse");
    const current = $select.val() || "";
    if ($select.find("option").length <= 1) {
      (data.warehouses || []).forEach((row) => $select.append(`<option value="${esc(row.name)}">${esc(warehouseLabel(row))}</option>`));
      $select.val(current);
    }
    const view = $root.find(".wafd-inventory-tabs button.is-active").data("view") || "all";
    const balances = (data.balances || []).filter((row) => view !== "low" || row.is_low || row.is_zero);
    const expiry = data.expiry_alerts || [];
    if (view === "expiry") {
      $root.find("#wafd-balance-results").html(!expiry.length ? '<div class="wafd-storekeeper-empty">لا توجد مواد منتهية أو قريبة من الانتهاء خلال 30 يوماً.</div>' : expiry.map((row) => `<div class="wafd-expiry-row ${Number(row.days_remaining) < 0 ? "is-expired" : ""}"><div><b>${esc(row.ingredient)}</b><small>${esc(row.warehouse)} · ${esc(row.quantity)} ${esc(row.uom || "")}</small></div><span>${Number(row.days_remaining) < 0 ? `منتهية منذ ${esc(Math.abs(row.days_remaining))} يوم` : `باقي ${esc(row.days_remaining)} يوم`}</span></div>`).join(""));
      return;
    }
    $root.find("#wafd-balance-results").html(!balances.length ? '<div class="wafd-storekeeper-empty">لا توجد أرصدة مطابقة.</div>' : balances.map((row) => `<div class="wafd-storekeeper-balance-row ${row.is_zero ? "is-zero" : row.is_low ? "is-low" : ""}"><span data-label="الصنف"><b>${esc(row.ingredient)}</b><small>${esc(row.category || "")} · ${esc(row.uom || "")}</small></span><span data-label="المكان">${esc(row.warehouse)}</span><span data-label="المتاح" class="is-available">${esc(row.available_quantity || 0)}</span><span data-label="الحد الأدنى">${esc(row.minimum_stock || 0)}</span></div>`).join(""));
  }

  async function loadSnapshot() {
    const serial = ++snapshotSerial;
    $root.find("#wafd-balance-results").addClass("is-loading");
    const response = await api("get_storekeeper_snapshot", {warehouse: $root.find("#wafd-balance-warehouse").val() || null, search: $root.find("#wafd-balance-search").val() || null});
    if (serial !== snapshotSerial) return;
    $root.find("#wafd-balance-results").removeClass("is-loading");
    renderInventory(response.message || {});
  }

  function runRequestedAction() {
    const action = localStorage.getItem("wafd_storekeeper_action");
    if (!action) return;
    localStorage.removeItem("wafd_storekeeper_action");
    if (action === "receive") openReceipt();
    if (action === "handover") openHandover();
    if (action === "inventory") showInventory();
  }

  renderShell();
  wrapper.wafd_run_storekeeper_action = runRequestedAction;
  setTimeout(runRequestedAction, 0);
};

frappe.pages["wafd-storekeeper-home"].on_page_show = function (wrapper) {
  wrapper.wafd_run_storekeeper_action?.();
};
