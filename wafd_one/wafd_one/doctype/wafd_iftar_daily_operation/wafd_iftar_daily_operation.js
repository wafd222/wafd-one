frappe.ui.form.on("WAFD Iftar Daily Operation", {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.dashboard.add_indicator(__(`المخطط: ${frm.doc.planned_meals || 0}`), "blue");
    frm.dashboard.add_indicator(__(`المستلم: ${frm.doc.received_meals || 0}`), (frm.doc.received_meals || 0) >= (frm.doc.planned_meals || 0) ? "green" : "orange");

    frm.add_custom_button(__("نموذج التسليم والاستلام"), () => {
      frappe.set_route("print", frm.doctype, frm.doc.name, { print_format: "إفطار صائم — تسليم واستلام يومي" });
    }, __("الطباعة / Print"));

    if (frm.doc.docstatus === 0) {
      const saveStage = async (field, source, label) => {
        const value = source ? (frm.doc[source] || 0) : (frm.doc.planned_meals || 0);
        await frm.set_value(field, value);
        await frm.save();
        frappe.show_alert({ message: label, indicator: "green" }, 4);
      };
      frm.add_custom_button(__("اعتماد الإنتاج"), () => saveStage("produced_meals", null, __("تم تسجيل الإنتاج")), __("مراحل التنفيذ"));
      frm.add_custom_button(__("اعتماد التغليف"), () => saveStage("packaged_meals", "produced_meals", __("تم تسجيل التغليف")), __("مراحل التنفيذ"));
      frm.add_custom_button(__("اعتماد التحميل"), () => saveStage("loaded_meals", "packaged_meals", __("تم تسجيل التحميل")), __("مراحل التنفيذ"));
      frm.add_custom_button(__("اعتماد التسليم"), () => saveStage("delivered_meals", "loaded_meals", __("تم تسجيل التسليم")), __("مراحل التنفيذ"));
      frm.add_custom_button(__("اعتماد الاستلام"), async () => {
        if (!frm.doc.recipient_name) {
          frappe.msgprint(__("أدخل اسم المستلم قبل اعتماد الاستلام."));
          return;
        }
        await saveStage("received_meals", "delivered_meals", __("تم تسجيل الاستلام"));
      }, __("مراحل التنفيذ"));
    }
  }
});
