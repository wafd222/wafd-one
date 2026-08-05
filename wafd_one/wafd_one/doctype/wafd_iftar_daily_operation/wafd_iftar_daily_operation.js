frappe.ui.form.on("WAFD Iftar Daily Operation", {
  refresh(frm) {
    if (!frm.is_new()) {
      frm.dashboard.add_indicator(__(`المخطط: ${frm.doc.planned_meals || 0}`), "blue");
      frm.dashboard.add_indicator(__(`المستلم: ${frm.doc.received_meals || 0}`), frm.doc.received_meals >= frm.doc.planned_meals ? "green" : "orange");
      frm.add_custom_button(__("نموذج التسليم / Delivery Form"), () => frappe.set_route("print", frm.doctype, frm.doc.name), __("الطباعة / Print"));
    }
  }
});
