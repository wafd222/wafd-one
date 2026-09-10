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

  function openCleaningHandover() {
    frappe.call({
      method: "wafd_one.storekeeper_portal.get_cleaning_handover_options",
      freeze: true,
      callback(r) {
        const base = r.message || {};
        if (!(base.warehouses || []).length) {
          frappe.msgprint(__("لا يوجد مستودع نظافة نشط. أضف أو فعّل مستودع النظافة أولاً."));
          return;
        }
        if (!(base.supervisors || []).length) {
          frappe.msgprint(__("لا يوجد مستخدم نشط بدور مشرف النظافة."));
          return;
        }
        let dialog;
        const loadItems = (warehouse) => {
          const $box = dialog.fields_dict.materials_html.$wrapper;
          $box.html('<div class="wafd-storekeeper-loading">جارٍ تحميل المواد المتاحة…</div>');
          frappe.call({
            method: "wafd_one.storekeeper_portal.get_cleaning_handover_options",
            args: { warehouse },
            callback(itemsResponse) {
              const items = (itemsResponse.message || {}).items || [];
              if (!items.length) {
                $box.html('<div class="wafd-cleaning-no-stock">لا توجد مواد متاحة في هذا المستودع. يجب استلام المواد وإضافتها للمخزون أولاً.</div>');
                return;
              }
              $box.html(`<div class="wafd-cleaning-pick-head">اختر المواد ذات الرصيد المتاح ثم أدخل الكمية والسعر</div>${items.map((item) => `
                <label class="wafd-cleaning-pick-row ${item.can_issue ? "" : "is-unavailable"}" data-ingredient="${escape(item.ingredient)}">
                  <input type="checkbox" class="wafd-cleaning-check" ${item.can_issue ? "" : "disabled"}>
                  <span><b>${escape(item.ingredient)}</b><small>${escape(item.category || "")} · ${item.can_issue ? `المتاح: ${escape(item.available_quantity)} ${escape(item.uom || "")}` : "الرصيد صفر — استلم المادة أولاً"}</small></span>
                  <input class="wafd-cleaning-qty" type="number" inputmode="decimal" min="0" max="${escape(item.available_quantity)}" step="any" placeholder="الكمية" ${item.can_issue ? "" : "disabled"}>
                  <input class="wafd-cleaning-price" type="number" inputmode="decimal" min="0" step="any" value="${escape(item.unit_cost || 0)}" placeholder="السعر" ${item.can_issue ? "" : "disabled"}>
                </label>`).join("")}`);
            },
          });
        };
        dialog = new frappe.ui.Dialog({
          title: __("إرسال مواد لمشرف النظافة"),
          fields: [
            { fieldname: "source_warehouse", fieldtype: "Select", label: __("مستودع النظافة"), reqd: 1, options: (base.warehouses || []).map((row) => row.name), onchange() { loadItems(dialog.get_value("source_warehouse")); } },
            { fieldname: "issued_to_user", fieldtype: "Select", label: __("مشرف النظافة المستلم"), reqd: 1, options: (base.supervisors || []).map((row) => row.name) },
            { fieldname: "materials_html", fieldtype: "HTML" },
          ],
          size: "large",
          primary_action_label: __("إرسال وتحديث الرصيد"),
          primary_action(values) {
            const selected = [];
            dialog.fields_dict.materials_html.$wrapper.find(".wafd-cleaning-pick-row").each(function () {
              const $row = $(this);
              if (!$row.find(".wafd-cleaning-check").prop("checked")) return;
              const quantity = Number($row.find(".wafd-cleaning-qty").val() || 0);
              const unitCost = Number($row.find(".wafd-cleaning-price").val() || 0);
              if (quantity > 0) selected.push({ ingredient: $row.data("ingredient"), quantity, unit_cost: unitCost });
            });
            if (!selected.length) {
              frappe.msgprint(__("اختر مادة واحدة على الأقل واكتب الكمية."));
              return;
            }
            frappe.call({
              method: "wafd_one.storekeeper_portal.create_cleaning_handover",
              args: { source_warehouse: values.source_warehouse, issued_to_user: values.issued_to_user, items: JSON.stringify(selected) },
              freeze: true,
              freeze_message: __("جارٍ إرسال المواد وتحديث الرصيد…"),
              callback(result) {
                if (!result.message) return;
                dialog.hide();
                frappe.show_alert({ message: __("تم إرسال المواد للمشرف بانتظار تأكيد الاستلام"), indicator: "green" }, 5);
                loadBalances();
              },
            });
          },
        });
        dialog.show();
        dialog.set_value("source_warehouse", base.warehouses[0].name);
        dialog.set_value("issued_to_user", base.supervisors[0].name);
        loadItems(base.warehouses[0].name);
      },
    });
  }

  function renderShell() {
    $root.html(`<style>
      .wafd-storekeeper-actions{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}
      .wafd-storekeeper-handovers{margin-top:14px}
      .wafd-handover-row{display:grid;grid-template-columns:1.2fr auto;gap:8px;border:1px solid #e8e1d4;border-radius:14px;margin-top:10px;padding:12px}
      .wafd-handover-row small{display:block;color:#777}.wafd-handover-row .status{background:#f1e7ce;color:#73591f;border-radius:14px;padding:5px 9px;font-size:11px}
      .wafd-handover-row p{grid-column:1/-1;margin:0;color:#555}.wafd-handover-row .usage{color:#267048;background:#edf7f1;border-radius:8px;padding:7px}
      .wafd-cleaning-pick-head{font-weight:800;margin:8px 0}.wafd-cleaning-pick-row{display:grid;grid-template-columns:auto minmax(170px,1fr) 105px 105px;gap:8px;align-items:center;border:1px solid #e7dfcf;border-radius:12px;padding:10px;margin:8px 0}.wafd-cleaning-pick-row span small{display:block;color:#777}.wafd-cleaning-pick-row input[type=number]{width:100%;border:1px solid #d8d1c4;border-radius:9px;padding:8px}.wafd-cleaning-no-stock{background:#fff4df;color:#785916;border-radius:12px;padding:16px;text-align:center}@media(max-width:600px){.wafd-cleaning-pick-row{grid-template-columns:auto 1fr}.wafd-cleaning-pick-row input[type=number]{grid-column:auto/span 1}}
      .wafd-cleaning-pick-row.is-unavailable{opacity:.58;background:#f5f5f5}
    </style>
      <div class="wafd-storekeeper-wrap">
        <section class="wafd-storekeeper-head">
          <div><span>إدارة مبسطة للمستودع</span><h2>اختر العملية المطلوبة</h2></div>
          <button type="button" data-action="movements">سجل الحركات</button>
        </section>
        <section class="wafd-storekeeper-actions">
          <button class="is-primary" type="button" data-action="receipt"><b>＋</b><strong>استلام مواد مشتراة</strong><small>اختيار أمر الشراء والمستودع ثم تسجيل الكمية</small></button>
          <button type="button" data-action="issue"><b>−</b><strong>صرف مواد</strong><small>صرف الأصناف من المستودع إلى المستلم</small></button>
          <button type="button" data-action="cleaning"><b>➜</b><strong>إرسال لمشرف النظافة</strong><small>اختيار قسم النظافة ثم إرسال المواد لتأكيد الاستلام</small></button>
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
        <section class="wafd-storekeeper-balances wafd-storekeeper-handovers">
          <div class="wafd-storekeeper-balance-head"><div><span>تسليمات مشرفي النظافة</span><small>حالة الاستلام وأغراض الصرف المسجلة</small></div></div>
          <div id="wafd-handover-results" class="wafd-storekeeper-results"><div class="wafd-storekeeper-loading">جارٍ تحميل التسليمات…</div></div>
        </section>
      </div>`);

    $root.on("click", "[data-action='receipt']", () => openMovement("استلام / Receipt", { reference_type: "WAFD Purchase Order" }));
    $root.on("click", "[data-action='issue']", () => openMovement("صرف / Issue"));
    $root.on("click", "[data-action='cleaning']", openCleaningHandover);
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
    } else {
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

    const handovers = data.cleaning_handovers || [];
    $root.find("#wafd-handover-results").html(!handovers.length ? '<div class="wafd-storekeeper-empty">لا توجد تسليمات نظافة حتى الآن.</div>' : handovers.map((row) => `
      <div class="wafd-handover-row">
        <div><b>${escape(row.name)}</b><small>${escape(row.issued_to_user || "")} · ${escape(row.posting_date || "")}</small></div>
        <span class="status">${escape(row.handover_status)}</span>
        <p>${(row.items || []).map((i) => `${escape(i.ingredient)}: ${escape(i.quantity)} ${escape(i.uom || "")}`).join("، ")}</p>
        <p class="usage">${(row.usage || []).length ? (row.usage || []).map((u) => `صرف: ${(u.items || []).map((i) => `${escape(i.ingredient)} ${escape(i.quantity)} ${escape(i.uom || "")}`).join("، ")} — ${escape(u.purpose)}${u.location ? ` — ${escape(u.location)}` : ""}`).join(" | ") : "لم يسجل المشرف صرفاً بعد"}</p>
      </div>`).join(""));
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
  wrapper.wafd_open_cleaning_handover = openCleaningHandover;
  if (localStorage.getItem("wafd_open_cleaning_handover") === "1") {
    localStorage.removeItem("wafd_open_cleaning_handover");
    openCleaningHandover();
  }
};

frappe.pages["wafd-storekeeper-home"].on_page_show = function (wrapper) {
  if (localStorage.getItem("wafd_open_cleaning_handover") === "1" && wrapper.wafd_open_cleaning_handover) {
    localStorage.removeItem("wafd_open_cleaning_handover");
    wrapper.wafd_open_cleaning_handover();
  }
};
