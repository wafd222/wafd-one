const WAFD_MENU_SOURCE = "منيو وفد المدينة / WAFD Menu";

function quotation_api(frm, method, args = {}) {
  return frappe.call({
    method: `wafd_one.wafd_one.doctype.wafd_quotation.wafd_quotation.${method}`,
    args: { name: frm.doc.name, ...args },
    freeze: true,
    freeze_message: __("جارٍ تحديث عرض السعر… / Updating quotation…"),
  }).then(() => frm.reload_doc());
}

function calculate_quotation(frm) {
  let days = 0;
  if (frm.doc.start_date && frm.doc.end_date) {
    days = Math.max(frappe.datetime.get_day_diff(frm.doc.end_date, frm.doc.start_date) + 1, 0);
  }
  frm.doc.service_days = days;
  let rows_total = 0;
  (frm.doc.items || []).forEach((row) => {
    row.service_days = days;
    row.daily_quantity = flt(row.daily_quantity || frm.doc.beneficiary_count);
    row.total_quantity = row.daily_quantity * days;
    row.amount = row.total_quantity * flt(row.unit_price);
    rows_total += row.amount;
  });
  const subtotal = rows_total + flt(frm.doc.additional_charges);
  const taxable = Math.max(subtotal - flt(frm.doc.discount_amount), 0);
  const tax = taxable * flt(frm.doc.tax_rate || 15) / 100;
  frm.doc.subtotal = subtotal;
  frm.doc.tax_amount = tax;
  frm.doc.grand_total = taxable + tax;
  frm.refresh_fields(["service_days", "items", "subtotal", "tax_amount", "grand_total"]);
}

function add_asset_toggle(frm, fieldname, show_label, hide_label, icon) {
  const shown = cint(frm.doc[fieldname]);
  frm.add_custom_button(`${icon} ${shown ? hide_label : show_label}`, async () => {
    await frm.set_value(fieldname, shown ? 0 : 1);
    if (!frm.is_new()) await frm.save();
    frappe.show_alert({ message: shown ? __("تم الإخفاء من عرض السعر مع الاحتفاظ بالملف") : __("تم الإظهار في عرض السعر"), indicator: "green" });
  }, __("التوقيع والختم / Signature & Stamp"));
}

function quotation_preview_url(name) {
  return `/api/method/wafd_one.wafd_one.doctype.wafd_quotation.wafd_quotation.preview_quotation_html?${new URLSearchParams({ name })}`;
}

function quotation_pdf_url(name, download = false) {
  const query = new URLSearchParams({ name });
  if (download) query.set("download", "1");
  return `/api/method/wafd_one.wafd_one.doctype.wafd_quotation.wafd_quotation.download_generated_pdf?${query}`;
}

async function generate_quotation_pdf(frm) {
  if (frm.is_dirty()) await frm.save();
  const response = await frappe.call({
    method: "wafd_one.wafd_one.doctype.wafd_quotation.wafd_quotation.generate_quotation_pdf",
    args: { name: frm.doc.name }, freeze: true,
    freeze_message: __("جارٍ تجهيز ملف PDF… / Preparing PDF…"),
  });
  await frm.reload_doc();
  return response.message || null;
}

async function share_quotation_pdf(frm) {
  const result = await generate_quotation_pdf(frm);
  if (!result?.file_url) return;
  const response = await fetch(quotation_pdf_url(frm.doc.name), { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) throw new Error("PDF fetch failed");
  const blob = await response.blob();
  const file = new File([blob], result.file_name || `${frm.doc.name}.pdf`, { type: "application/pdf" });
  if (navigator.share && (!navigator.canShare || navigator.canShare({ files: [file] }))) {
    await navigator.share({ title: frm.doc.customer_name || frm.doc.name, files: [file] });
    return;
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = file.name; link.style.display = "none";
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function install_quotation_preview_style() {
  if (document.getElementById("wafd-quotation-preview-style")) return;
  const style = document.createElement("style");
  style.id = "wafd-quotation-preview-style";
  style.textContent = `
    .wafd-q-preview{position:fixed;inset:0;z-index:1060;background:#fff;display:flex;flex-direction:column;overscroll-behavior:none}
    .wafd-q-head{height:54px;min-height:54px;display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #ddd;background:#fff;direction:rtl}
    .wafd-q-title{font-size:16px;font-weight:700}.wafd-q-close{width:38px;height:38px;border:1px solid #e1dccf;border-radius:11px;background:#fff;font-size:24px;line-height:1}
    .wafd-q-tools{height:42px;min-height:42px;display:flex;align-items:center;justify-content:center;gap:8px;background:#f7f7f7;border-bottom:1px solid #ddd;direction:ltr}
    .wafd-q-tools button{height:32px;min-width:38px;border:1px solid #d5d5d5;border-radius:9px;background:#fff}.wafd-q-fit{padding:0 11px;font-weight:700}.wafd-q-label{min-width:52px;text-align:center;font-size:12px;font-weight:700}
    .wafd-q-frame{flex:1;min-height:0;width:100%;border:0;background:#eee}.wafd-q-actions{display:flex;gap:8px;padding:10px 12px calc(10px + env(safe-area-inset-bottom));border-top:1px solid #ddd;background:#fff;direction:rtl}.wafd-q-actions .btn{flex:1;min-height:44px}
  `;
  document.head.appendChild(style);
}

function open_quotation_preview(frm) {
  if (frm.is_new()) { frappe.msgprint(__("احفظ عرض السعر أولاً ثم افتح المعاينة.")); return; }
  install_quotation_preview_style();
  document.querySelector(".wafd-q-preview")?.remove();
  const overlay = document.createElement("div");
  overlay.className = "wafd-q-preview";
  overlay.innerHTML = `
    <div class="wafd-q-head"><div class="wafd-q-title">${__("معاينة عرض السعر")}</div><button class="wafd-q-close" aria-label="${__("رجوع")}">×</button></div>
    <div class="wafd-q-tools"><button class="wafd-q-out">−</button><span class="wafd-q-label">100%</span><button class="wafd-q-in">+</button><button class="wafd-q-fit">${__("ملاءمة الشاشة")}</button></div>
    <iframe class="wafd-q-frame" sandbox="allow-same-origin" title="${__("معاينة عرض السعر")}"></iframe>
    <div class="wafd-q-actions"><button class="btn btn-primary wafd-q-print">${__("طباعة PDF")}</button><button class="btn btn-default wafd-q-share">${__("مشاركة PDF")}</button></div>`;
  document.body.appendChild(overlay);
  const frame = overlay.querySelector(".wafd-q-frame");
  const label = overlay.querySelector(".wafd-q-label");
  let stage, viewport, scale = 1, fit = 1;
  const applyScale = (value) => {
    if (!stage || !viewport) return;
    scale = Math.max(fit * .8, Math.min(4, value));
    stage.style.transform = `scale(${scale})`;
    viewport.style.width = `${Math.ceil(stage.__w * scale)}px`;
    viewport.style.height = `${Math.ceil(stage.__h * scale)}px`;
    label.textContent = `${Math.round(scale / fit * 100)}%`;
  };
  frame.addEventListener("load", () => setTimeout(() => {
    try {
      const doc = frame.contentDocument;
      doc.documentElement.style.overflow = "auto"; doc.body.style.margin = "0"; doc.body.style.padding = "0"; doc.body.style.background = "#eee";
      const nodes = Array.from(doc.body.childNodes);
      viewport = doc.createElement("div"); viewport.style.position = "relative"; viewport.style.margin = "10px auto 24px";
      stage = doc.createElement("div"); stage.style.position = "absolute"; stage.style.left = "0"; stage.style.top = "0"; stage.style.transformOrigin = "top left";
      nodes.forEach((node) => stage.appendChild(node)); viewport.appendChild(stage); doc.body.appendChild(viewport);
      const rect = stage.getBoundingClientRect(); stage.__w = Math.max(stage.scrollWidth, rect.width, 794); stage.__h = Math.max(stage.scrollHeight, rect.height, 1123);
      stage.style.width = `${stage.__w}px`; fit = Math.min(1, Math.max(280, frame.clientWidth - 20) / stage.__w); applyScale(fit);
    } catch (_e) {}
  }, 120));
  frame.src = `${quotation_preview_url(frm.doc.name)}&t=${Date.now()}`;
  overlay.querySelector(".wafd-q-out").onclick = () => applyScale(scale / 1.2);
  overlay.querySelector(".wafd-q-in").onclick = () => applyScale(scale * 1.2);
  overlay.querySelector(".wafd-q-fit").onclick = () => applyScale(fit);
  overlay.querySelector(".wafd-q-close").onclick = () => overlay.remove();
  overlay.querySelector(".wafd-q-print").onclick = async () => {
    const target = window.open("", "_blank");
    try {
      const result = await generate_quotation_pdf(frm);
      if (result && target) target.location = quotation_pdf_url(frm.doc.name);
      else if (result) window.location.assign(quotation_pdf_url(frm.doc.name));
      else target?.close();
    }
    catch (_e) { target?.close(); }
  };
  overlay.querySelector(".wafd-q-share").onclick = async () => {
    try { await share_quotation_pdf(frm); } catch (error) { if (error?.name !== "AbortError") frappe.msgprint(__("تعذر تجهيز ملف PDF للمشاركة.")); }
  };
}

frappe.ui.form.on("WAFD Quotation", {
  onload(frm) {
    if (frm.is_new() && !frm.doc.valid_until) {
      const base = frm.doc.quotation_date || frappe.datetime.get_today();
      frm.set_value("valid_until", frappe.datetime.add_days(base, 15));
    }
  },
  setup(frm) {
    frm.set_query("wafd_menu", "items", () => ({ filters: { status: "نشطة / Active" } }));
  },
  refresh(frm) {
    calculate_quotation(frm);
    add_asset_toggle(frm, "include_signature", "إظهار التوقيع", "إخفاء التوقيع", "✍️");
    add_asset_toggle(frm, "include_stamp", "إظهار الختم", "إخفاء الختم", "◉");
    if (!frm.is_new()) {
      frm.add_custom_button(__("معاينة عرض السعر / Preview"), async () => {
        if (frm.is_dirty()) await frm.save();
        open_quotation_preview(frm);
      });
    }
    if (!frm.is_new() && frm.doc.status === "مسودة / Draft") {
      frm.add_custom_button(__("إرسال للاعتماد / Request Approval"), () => quotation_api(frm, "request_approval"), __("الإجراءات / Actions"));
    }
    const roles = new Set(frappe.user_roles || []);
    if (!frm.is_new() && frm.doc.status === "بانتظار الاعتماد / Pending Approval" && ["System Manager", "WAFD Operations Manager", "WAFD Approver"].some((role) => roles.has(role))) {
      frm.add_custom_button(__("اعتماد عرض السعر / Approve"), () => quotation_api(frm, "approve_quotation"), __("الإجراءات / Actions"));
    }
    if (!frm.is_new() && ["معتمد / Approved", "أرسل للعميل / Sent", "مقبول / Accepted"].includes(frm.doc.status)) {
      const transitions = {
        "معتمد / Approved": [["أرسل للعميل / Mark Sent", "أرسل للعميل / Sent"], ["إلغاء / Cancel", "ملغي / Cancelled"]],
        "أرسل للعميل / Sent": [["مقبول / Accepted", "مقبول / Accepted"], ["مرفوض / Rejected", "مرفوض / Rejected"], ["إلغاء / Cancel", "ملغي / Cancelled"]],
        "مقبول / Accepted": [["إلغاء / Cancel", "ملغي / Cancelled"]],
      };
      (transitions[frm.doc.status] || []).forEach(([label, status]) => {
        frm.add_custom_button(__(label), () => quotation_api(frm, "set_quotation_status", { status }), __("الحالة / Status"));
      });
    }
  },
  customer_company(frm) {
    if (!frm.doc.customer_company) return;
    frappe.db.get_value("WAFD Mission", frm.doc.customer_company, ["mission_name", "official_name", "contact_person", "mobile", "email", "address"]).then(({ message }) => {
      if (!message) return;
      frm.set_value("customer_name", message.official_name || message.mission_name);
      frm.set_value("contact_person", message.contact_person);
      frm.set_value("customer_phone", message.mobile);
      frm.set_value("customer_email", message.email);
      if (!frm.doc.supply_location) frm.set_value("supply_location", message.address);
    });
  },
  start_date: calculate_quotation,
  end_date: calculate_quotation,
  beneficiary_count: calculate_quotation,
  additional_charges: calculate_quotation,
  discount_amount: calculate_quotation,
  tax_rate: calculate_quotation,
  items_add(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    row.daily_quantity = frm.doc.beneficiary_count || 0;
    row.service_days = frm.doc.service_days || 0;
    row.menu_source = WAFD_MENU_SOURCE;
    calculate_quotation(frm);
  },
});

frappe.ui.form.on("WAFD Quotation Item", {
  menu_source(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.menu_source !== WAFD_MENU_SOURCE) {
      frappe.model.set_value(cdt, cdn, "wafd_menu", "");
      frappe.model.set_value(cdt, cdn, "menu_description", row.custom_menu_description || "");
    }
  },
  wafd_menu(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.wafd_menu) return;
    frappe.db.get_value("WAFD Recipe", row.wafd_menu, ["recipe_name", "recommended_price_ex_vat"]).then(({ message }) => {
      if (!message) return;
      frappe.model.set_value(cdt, cdn, "menu_description", message.recipe_name || row.wafd_menu);
      if (!flt(row.unit_price) && flt(message.recommended_price_ex_vat)) {
        frappe.model.set_value(cdt, cdn, "unit_price", message.recommended_price_ex_vat);
      }
      calculate_quotation(frm);
    });
  },
  custom_menu_description(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.menu_source !== WAFD_MENU_SOURCE) frappe.model.set_value(cdt, cdn, "menu_description", row.custom_menu_description || "");
  },
  daily_quantity: calculate_quotation,
  unit_price: calculate_quotation,
  items_remove: calculate_quotation,
});
