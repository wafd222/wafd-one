frappe.pages["wafd-storekeeper-home"].on_page_load = function (wrapper) {
  let lang = localStorage.getItem("wafd_lang") || "ar";
  const tr = (ar, en) => lang === "ar" ? ar : en;
  const page = frappe.ui.make_app_page({parent: wrapper, title: tr("شاشة أمين المستودع", "Storekeeper"), single_column: true});
  const $root = $(page.body).addClass("wafd-storekeeper-home").attr("dir", lang === "ar" || lang === "ur" ? "rtl" : "ltr");
  const esc = (value) => frappe.utils.escape_html(String(value == null ? "" : value));
  let snapshotSerial = 0;

  const api = (method, args = {}, options = {}) => frappe.call({
    method: `wafd_one.storekeeper_portal.${method}`,
    args,
    freeze: Boolean(options.freeze),
    freeze_message: options.message,
  });
  const localData = (value) => {
    const parts = String(value || "").split("/").map((part) => part.trim());
    return parts.length > 1 ? (lang === "ar" ? parts[0] : parts[parts.length - 1]) : String(value || "");
  };
  const warehouseLabel = (row) => `${row.warehouse_name || row.name} — ${localData(row.warehouse_type)}`;
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
      $box.html(`<div class="wafd-storekeeper-empty">${esc(tr("لا توجد مواد مطابقة. جرّب قسماً آخر أو كلمة بحث مختلفة.", "No matching materials. Try another category or search term."))}</div>`);
      return;
    }
    $box.html(rows.map((item) => {
      const saved = selected.get(item.ingredient) || {};
      const available = Number(item.available_quantity || 0);
      return `<div class="wafd-material-card ${saved.ingredient ? "is-selected" : ""}" data-ingredient="${esc(item.ingredient)}">
        <input class="wafd-material-check" type="checkbox" ${saved.ingredient ? "checked" : ""}>
        <div class="wafd-material-name"><strong>${esc(item.ingredient_label || item.ingredient)}</strong><small>${esc(localData(item.category) || tr("بدون قسم", "Uncategorized"))} · ${esc(localData(item.uom))}${mode === "handover" ? ` · ${esc(tr("المتاح", "Available"))} ${esc(available)}` : ""}</small></div>
        <label><span>${esc(tr("الكمية", "Quantity"))}</span><input class="wafd-material-qty" type="number" inputmode="decimal" min="0" ${mode === "handover" ? `max="${esc(available)}"` : ""} step="any" value="${esc(saved.quantity || "")}" placeholder="0"></label>
        <label><span>${esc(tr("سعر الوحدة", "Unit price"))}</span><input class="wafd-material-price" type="number" inputmode="decimal" min="0" step="any" value="${esc(saved.unit_cost == null ? item.unit_cost || 0 : saved.unit_cost)}"></label>
        ${mode === "receipt" ? `<label class="wafd-expiry-field"><span>${esc(tr("تاريخ الانتهاء (اختياري)", "Expiry date (optional)"))}</span><input class="wafd-material-expiry" type="date" value="${esc(saved.expiry_date || "")}"></label>` : ""}
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
    const base = (await api("get_storekeeper_workflow_options", {receipt: 1, language: lang}, {freeze: true})).message || {};
    if (!(base.warehouses || []).length) return frappe.msgprint(tr("لا يوجد مستودع أو ثلاجة نشطة.", "No active warehouse or cold room exists."));
    const selected = new Map();
    let searchTimer;
    const dialog = new frappe.ui.Dialog({
      title: tr("استلام وتوزيع المشتريات", "Receive and Distribute Purchases"), size: "large",
      fields: [{fieldname: "guided_receipt", fieldtype: "HTML"}],
      primary_action_label: tr("إضافة المواد للمخزون", "Add materials to inventory"),
      primary_action: async () => {
        const $panel = dialog.fields_dict.guided_receipt.$wrapper;
        readSelected($panel.find("#wafd-receipt-items"), selected, "receipt");
        const target = $panel.find("#wafd-receipt-warehouse").val();
        const rows = [...selected.values()].filter((row) => row.quantity > 0);
        if (!target) return frappe.msgprint(tr("اختر المستودع أو الثلاجة التي ستوضع فيها المواد.", "Choose the destination warehouse or cold room."));
        if (!rows.length) return frappe.msgprint(tr("اختر مادة واحدة على الأقل واكتب الكمية.", "Select at least one material and enter its quantity."));
        const result = await api("receive_inventory_materials", {target_warehouse: target, items: JSON.stringify(rows)}, {freeze: true, message: tr("جارٍ إضافة المواد وتحديث المخزون…", "Adding materials and updating inventory…")});
        if (!result.message) return;
        dialog.hide();
        frappe.show_alert({message: tr(`تمت إضافة ${result.message.items_count} مادة إلى ${result.message.warehouse}`, `${result.message.items_count} materials were added to ${result.message.warehouse}`), indicator: "green"}, 6);
        loadSnapshot();
      },
    });
    dialog.show();
    const $panel = dialog.fields_dict.guided_receipt.$wrapper;
    $panel.html(`<div class="wafd-guided-panel">
      <div class="wafd-step"><b>1</b><div><strong>${esc(tr("أين ستوضع المواد؟", "Where will the materials be stored?"))}</strong><small>${esc(tr("اختر المستودع أو الثلاجة مباشرة ويمكن تغييره دون مسح النص.", "Choose a warehouse or cold room; you can change it directly."))}</small></div></div>
      <select id="wafd-receipt-warehouse">${optionsHtml(base.warehouses || [], "name", warehouseLabel, tr("اختر المستودع أو الثلاجة", "Choose warehouse or cold room"))}</select>
      <div class="wafd-step"><b>2</b><div><strong>${esc(tr("مواد هذا المستودع", "Materials in this warehouse"))}</strong><small>${esc(tr("تظهر المواد المطابقة للمستودع مباشرة؛ ابحث بالاسم عند الحاجة ثم أدخل الكمية والسعر.", "Matching materials appear immediately; search by name when needed, then enter quantity and price."))}</small></div></div>
      <div class="wafd-picker-filters wafd-receipt-search-only"><input id="wafd-receipt-search" type="search" placeholder="${esc(tr("ابحث باسم المادة أو رمزها", "Search by material name or code"))}"></div>
      <div id="wafd-receipt-items" class="wafd-material-results"><div class="wafd-picker-help">${esc(tr("اختر المستودع أو الثلاجة لتظهر مواده مباشرة.", "Choose a warehouse or cold room to show its materials."))}</div></div>
      <button type="button" class="wafd-secondary-link" id="wafd-open-orders">${esc(tr("عرض أوامر الشراء", "View purchase orders"))}</button>
    </div>`);
    const load = async () => {
      const search = $panel.find("#wafd-receipt-search").val().trim();
      const warehouse = $panel.find("#wafd-receipt-warehouse").val();
      const $box = $panel.find("#wafd-receipt-items");
      readSelected($box, selected, "receipt");
      if (!warehouse) return $box.html(`<div class="wafd-picker-help">${esc(tr("اختر المستودع أو الثلاجة أولاً.", "Choose a warehouse or cold room first."))}</div>`);
      $box.html(`<div class="wafd-storekeeper-loading">${esc(tr("جارٍ البحث…", "Searching…"))}</div>`);
      const response = await api("get_storekeeper_workflow_options", {warehouse, search: search || null, receipt: 1, language: lang});
      renderMaterialCards($box, (response.message || {}).items || [], selected, "receipt");
    };
    const refreshReceiptMaterials = async () => {
      selected.clear();
      $panel.find("#wafd-receipt-search").val("");
      await load();
    };
    $panel.on("change", "#wafd-receipt-warehouse", refreshReceiptMaterials);
    $panel.on("input", "#wafd-receipt-search", () => { clearTimeout(searchTimer); searchTimer = setTimeout(load, 250); });
    $panel.on("click", "#wafd-open-orders", () => frappe.set_route("List", "WAFD Purchase Order"));
  }

  async function openHandover() {
    const base = (await api("get_storekeeper_workflow_options", {language: lang}, {freeze: true})).message || {};
    if (!(base.warehouses || []).length) return frappe.msgprint(tr("لا يوجد مستودع أو ثلاجة نشطة.", "No active warehouse or cold room exists."));
    if (!(base.recipients || []).length) return frappe.msgprint(tr("لا يوجد موظفون نشطون في الوظائف المسموح التسليم لها.", "No active employees are available for material handover."));
    const selected = new Map();
    const roleEnglish = {
      "WAFD Cleaning Supervisor": "Cleaning Supervisor",
      "WAFD Production Supervisor": "Cooking Supervisor / Chef / Production Supervisor",
      "WAFD Project Manager": "Project Manager",
      "WAFD Quality Inspector": "Quality Inspector",
      "WAFD Delivery Supervisor": "Delivery Supervisor",
    };
    const roles = [...new Map((base.recipients || []).map((row) => [row.role, row.role_label])).entries()].map(([role, label]) => ({role, label: tr(label, roleEnglish[role] || role)}));
    let searchTimer;
    const dialog = new frappe.ui.Dialog({
      title: tr("تسليم مواد للموظفين", "Hand Over Materials to Employees"), size: "large",
      fields: [{fieldname: "guided_handover", fieldtype: "HTML"}],
      primary_action_label: tr("تسليم وتحديث الرصيد", "Hand over and update balance"),
      primary_action: async () => {
        const $panel = dialog.fields_dict.guided_handover.$wrapper;
        readSelected($panel.find("#wafd-handover-items"), selected, "handover");
        const role = $panel.find("#wafd-recipient-role").val();
        const recipient = $panel.find("#wafd-recipient-name").val();
        const source = $panel.find("#wafd-source-warehouse").val();
        const rows = [...selected.values()].filter((row) => row.quantity > 0);
        if (!role || !recipient) return frappe.msgprint(tr("اختر وظيفة المستلم ثم اسمه.", "Choose the recipient's job, then their name."));
        if (!source) return frappe.msgprint(tr("اختر المستودع أو الثلاجة المصدر.", "Choose the source warehouse or cold room."));
        if (!rows.length) return frappe.msgprint(tr("اختر مادة واحدة على الأقل واكتب الكمية.", "Select at least one material and enter its quantity."));
        const result = await api("create_employee_handover", {source_warehouse: source, issued_to_user: recipient, recipient_role: role, items: JSON.stringify(rows)}, {freeze: true, message: tr("جارٍ تسليم المواد وتحديث الرصيد…", "Handing over materials and updating inventory…")});
        if (!result.message) return;
        dialog.hide();
        frappe.show_alert({message: tr(`تم تسليم المواد إلى ${result.message.recipient}`, `Materials were handed over to ${result.message.recipient}`), indicator: "green"}, 6);
        loadSnapshot();
      },
    });
    dialog.show();
    const $panel = dialog.fields_dict.guided_handover.$wrapper;
    $panel.html(`<div class="wafd-guided-panel">
      <div class="wafd-step"><b>1</b><div><strong>${esc(tr("من هو المستلم؟", "Who will receive the materials?"))}</strong><small>${esc(tr("اختر الوظيفة أولاً ثم يظهر اسم الموظف، وليس البريد الإلكتروني.", "Choose the job first, then select the employee by name, not email."))}</small></div></div>
      <div class="wafd-picker-filters"><select id="wafd-recipient-role">${optionsHtml(roles, "role", (row) => localData(row.label), tr("اختر الوظيفة", "Choose job"))}</select><select id="wafd-recipient-name"><option value="">${esc(tr("اختر اسم المستلم", "Choose recipient name"))}</option></select></div>
      <div class="wafd-step"><b>2</b><div><strong>${esc(tr("من أين ستخرج المواد؟", "Where will the materials come from?"))}</strong><small>${esc(tr("اختر المستودع أو الثلاجة المصدر.", "Choose the source warehouse or cold room."))}</small></div></div>
      <select id="wafd-source-warehouse">${optionsHtml(base.warehouses || [], "name", warehouseLabel, tr("اختر المستودع أو الثلاجة", "Choose warehouse or cold room"))}</select>
      <div class="wafd-step"><b>3</b><div><strong>${esc(tr("اختر المواد", "Select materials"))}</strong><small>${esc(tr("اختر القسم أو ابحث، ولن تظهر إلا المواد ذات الرصيد المتاح.", "Choose a category or search; only available stock will appear."))}</small></div></div>
      <div class="wafd-picker-filters"><select id="wafd-handover-category" disabled><option value="">${esc(tr("اختر المستودع أولاً", "Choose a warehouse first"))}</option></select><input id="wafd-handover-search" type="search" placeholder="${esc(tr("ابحث باسم المادة أو رمزها", "Search by material name or code"))}"></div>
      <div id="wafd-handover-items" class="wafd-material-results"><div class="wafd-picker-help">${esc(tr("اختر المستودع ثم القسم، أو اكتب حرفين للبحث.", "Choose a warehouse and category, or type two characters."))}</div></div>
    </div>`);
    const updateNames = () => {
      const role = $panel.find("#wafd-recipient-role").val();
      const people = (base.recipients || []).filter((row) => row.role === role);
      $panel.find("#wafd-recipient-name").html(optionsHtml(people, "name", (row) => row.full_name, tr("اختر اسم المستلم", "Choose recipient name")));
    };
    const load = async () => {
      const warehouse = $panel.find("#wafd-source-warehouse").val();
      const category = $panel.find("#wafd-handover-category").val();
      const search = $panel.find("#wafd-handover-search").val().trim();
      const $box = $panel.find("#wafd-handover-items");
      readSelected($box, selected, "handover");
      if (!warehouse || (!category && search.length < 2)) return $box.html(`<div class="wafd-picker-help">${esc(tr("اختر المستودع ثم القسم، أو اكتب حرفين للبحث.", "Choose a warehouse and category, or type two characters."))}</div>`);
      $box.html(`<div class="wafd-storekeeper-loading">${esc(tr("جارٍ البحث في الرصيد المتاح…", "Searching available stock…"))}</div>`);
      const response = await api("get_storekeeper_workflow_options", {warehouse, category: category || null, search: search || null, language: lang});
      renderMaterialCards($box, (response.message || {}).items || [], selected, "handover");
    };
    const refreshHandoverCategories = async () => {
      const warehouse = $panel.find("#wafd-source-warehouse").val();
      const $category = $panel.find("#wafd-handover-category");
      selected.clear();
      $panel.find("#wafd-handover-items").html(`<div class="wafd-picker-help">${esc(tr("اختر المستودع ثم القسم، أو اكتب حرفين للبحث.", "Choose a warehouse and category, or type two characters."))}</div>`);
      if (!warehouse) return $category.prop("disabled", true).html(`<option value="">${esc(tr("اختر المستودع أولاً", "Choose a warehouse first"))}</option>`);
      const response = await api("get_storekeeper_workflow_options", {warehouse, language: lang});
      const categories = (response.message || {}).categories || [];
      $category.prop("disabled", false).html(optionsHtml(categories.map((category) => ({category})), "category", (row) => localData(row.category), tr("كل أقسام هذا المستودع", "All sections in this warehouse")));
    };
    $panel.on("change", "#wafd-recipient-role", updateNames);
    $panel.on("change", "#wafd-handover-category", load);
    $panel.on("change", "#wafd-source-warehouse", refreshHandoverCategories);
    $panel.on("input", "#wafd-handover-search", () => { clearTimeout(searchTimer); searchTimer = setTimeout(load, 250); });
  }

  function renderShell() {
    page.set_title(tr("شاشة أمين المستودع", "Storekeeper"));
    $root.attr("dir", lang === "ar" || lang === "ur" ? "rtl" : "ltr");
    $root.html(`<div class="wafd-storekeeper-wrap">
      <section class="wafd-storekeeper-head"><div><span>${esc(tr("إدارة عملية بدون نماذج معقدة", "Simple practical inventory management"))}</span><h2>${esc(tr("ماذا تريد أن تعمل الآن؟", "What do you want to do now?"))}</h2></div><button type="button" data-action="movements">${esc(tr("سجل الحركات", "Movement log"))}</button></section>
      <section class="wafd-storekeeper-actions wafd-three-actions">
        <button class="is-primary" type="button" data-action="receive"><b>＋</b><strong>${esc(tr("استلام وتوزيع المشتريات", "Receive and Distribute Purchases"))}</strong><small>${esc(tr("اختر المستودع أو الثلاجة، ثم ابحث عن المواد وسجّل الكمية والسعر.", "Choose a warehouse or cold room, find materials, and enter quantity and price."))}</small></button>
        <button type="button" data-action="handover"><b>➜</b><strong>${esc(tr("تسليم مواد للموظفين", "Hand Over Materials to Employees"))}</strong><small>${esc(tr("مشرف النظافة أو مشرف الطبخ والشيف وغيرهم، بالاسم والوظيفة.", "Select Cleaning Supervisor, Cooking Supervisor, Chef, or another employee by job and name."))}</small></button>
        <button type="button" data-action="inventory"><b>▣</b><strong>${esc(tr("معلومات المخزون", "Inventory Information"))}</strong><small>${esc(tr("كل الأرصدة والمواد الناقصة والمنتهية أو القريبة من الانتهاء.", "View balances, shortages, and expired or soon-to-expire materials."))}</small></button>
      </section>
      <section id="wafd-inventory-panel" class="wafd-storekeeper-balances" hidden>
        <div class="wafd-storekeeper-balance-head"><div><span>${esc(tr("معلومات المخزون", "Inventory Information"))}</span><small>${esc(tr("بحث وفلاتر وتنبيهات عملية", "Search, filters, and practical alerts"))}</small></div><button type="button" data-action="refresh">${esc(tr("تحديث", "Refresh"))}</button></div>
        <div id="wafd-inventory-summary" class="wafd-inventory-summary"></div>
        <div class="wafd-storekeeper-filters"><select id="wafd-balance-warehouse"><option value="">${esc(tr("كل المستودعات والثلاجات", "All warehouses and cold rooms"))}</option></select><input id="wafd-balance-search" type="search" placeholder="${esc(tr("ابحث باسم المادة أو المستودع", "Search by material or warehouse"))}"></div>
        <div class="wafd-inventory-tabs"><button class="is-active" data-view="all">${esc(tr("كل المواد", "All materials"))}</button><button data-view="low">${esc(tr("الناقص والصفر", "Low and zero stock"))}</button><button data-view="expiry">${esc(tr("قريب الانتهاء", "Expiring soon"))}</button></div>
        <div id="wafd-balance-results" class="wafd-storekeeper-results"><div class="wafd-storekeeper-loading">${esc(tr("جارٍ تحميل معلومات المخزون…", "Loading inventory information…"))}</div></div>
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
      [summary.materials || 0, tr("أرصدة مسجلة", "Recorded balances")], [summary.low || 0, tr("تحت الحد الأدنى", "Below minimum")],
      [summary.zero || 0, tr("رصيدها صفر", "Zero stock")], [(summary.expiring || 0) + (summary.expired || 0), tr("تنبيه انتهاء", "Expiry alerts")],
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
      $root.find("#wafd-balance-results").html(!expiry.length ? `<div class="wafd-storekeeper-empty">${esc(tr("لا توجد مواد منتهية أو قريبة من الانتهاء خلال 30 يوماً.", "No expired or expiring materials within 30 days."))}</div>` : expiry.map((row) => `<div class="wafd-expiry-row ${Number(row.days_remaining) < 0 ? "is-expired" : ""}"><div><b>${esc(row.ingredient_label || row.ingredient)}</b><small>${esc(row.warehouse)} · ${esc(row.quantity)} ${esc(localData(row.uom))}</small></div><span>${Number(row.days_remaining) < 0 ? tr(`منتهية منذ ${Math.abs(row.days_remaining)} يوم`, `Expired ${Math.abs(row.days_remaining)} days ago`) : tr(`باقي ${row.days_remaining} يوم`, `${row.days_remaining} days remaining`)}</span></div>`).join(""));
      return;
    }
    $root.find("#wafd-balance-results").html(!balances.length ? `<div class="wafd-storekeeper-empty">${esc(tr("لا توجد أرصدة مطابقة.", "No matching balances."))}</div>` : balances.map((row) => `<div class="wafd-storekeeper-balance-row ${row.is_zero ? "is-zero" : row.is_low ? "is-low" : ""}"><span data-label="${esc(tr("الصنف", "Material"))}"><b>${esc(row.ingredient_label || row.ingredient)}</b><small>${esc(localData(row.category))} · ${esc(localData(row.uom))}</small></span><span data-label="${esc(tr("المكان", "Location"))}">${esc(row.warehouse)}</span><span data-label="${esc(tr("المتاح", "Available"))}" class="is-available">${esc(row.available_quantity || 0)}</span><span data-label="${esc(tr("الحد الأدنى", "Minimum"))}">${esc(row.minimum_stock || 0)}</span></div>`).join(""));
  }

  async function loadSnapshot() {
    const serial = ++snapshotSerial;
    $root.find("#wafd-balance-results").addClass("is-loading");
    const response = await api("get_storekeeper_snapshot", {warehouse: $root.find("#wafd-balance-warehouse").val() || null, search: $root.find("#wafd-balance-search").val() || null, language: lang});
    if (serial !== snapshotSerial) return;
    $root.find("#wafd-balance-results").removeClass("is-loading");
    renderInventory(response.message || {});
  }

  function runRequestedAction() {
    const selectedLanguage = localStorage.getItem("wafd_lang") || "ar";
    if (selectedLanguage !== lang) {
      lang = selectedLanguage;
      renderShell();
    }
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
