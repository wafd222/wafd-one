frappe.ui.form.on("WAFD Iftar Daily Operation", {
  refresh(frm) {
    // The standard form is retained for administration audit and printing.
    // Production and every later action live only in the dedicated role pages.
    frm.$wrapper.find(".wafd-mobile-stage-action").remove();
    $(document.body).find(".wafd-mobile-stage-action").remove();
    frm.$wrapper.find(".form-layout").css("padding-bottom", "");
    if (frm.is_new()) return;

    const planned = Number(frm.doc.planned_meals || 0);
    const received = Number(frm.doc.received_meals || 0);
    frm.dashboard.add_indicator(__(`المخطط: ${planned}`), "blue");
    frm.dashboard.add_indicator(__(`المستلم: ${received}`), received >= planned && planned ? "green" : "orange");

    frm.add_custom_button(__("التقرير اليومي الرسمي"), () => {
      const query = new URLSearchParams({
        doctype: frm.doctype,
        name: frm.doc.name,
        format: "WAFD Iftar Official Daily Report",
        no_letterhead: "0",
      });
      window.open(`/api/method/frappe.utils.print_format.download_pdf?${query.toString()}`, "_blank", "noopener");
    }, __("الطباعة / Print"));

    frm.add_custom_button(__("نموذج التسليم والاستلام"), () => {
      frappe.route_options = {print_format: "إفطار صائم — تسليم واستلام يومي"};
      frappe.set_route("print", frm.doctype, frm.doc.name);
    }, __("الطباعة / Print"));
  },
});
