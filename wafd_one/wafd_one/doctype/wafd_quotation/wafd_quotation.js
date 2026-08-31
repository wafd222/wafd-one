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
        frm.print_doc();
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
