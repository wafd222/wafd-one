frappe.ui.form.on("WAFD Print Settings", {
  refresh(frm) {
    frm.set_intro(__("يمكنك تعديل شكل مستندات PDF دون تغيير الكود. احفظ الإعدادات ثم افتح المعاينة."), "blue");
  },
  preview_print(frm) {
    if (!frm.doc.preview_undertaking) {
      frappe.msgprint(__("اختر تعهدًا في حقل المعاينة أولًا."));
      return;
    }
    const url = `/printview?doctype=${encodeURIComponent("WAFD Hotel Undertaking")}&name=${encodeURIComponent(frm.doc.preview_undertaking)}&format=${encodeURIComponent("تعهد والتزام إعاشة — WAFD")}&no_letterhead=1`;
    window.open(url, "_blank");
  },
  reset_defaults(frm) {
    frappe.confirm(__("هل تريد إعادة إعدادات الطباعة إلى القيم الافتراضية؟"), () => {
      frappe.call({
        method: "wafd_one.wafd_one.doctype.wafd_print_settings.wafd_print_settings.reset_defaults",
        freeze: true,
        callback() { frm.reload_doc(); }
      });
    });
  }
});
