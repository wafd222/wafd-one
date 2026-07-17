frappe.ui.form.on("WAFD Invoice", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.status === "ملغاة / Cancelled") return;
        if (flt(frm.doc.balance) > 0) {
            frm.add_custom_button(__("Register Payment"), () => {
                frappe.new_doc("WAFD Payment", {
                    invoice: frm.doc.name,
                    project: frm.doc.project,
                    payment_date: frappe.datetime.get_today(),
                    amount: frm.doc.balance,
                    status: "مسودة / Draft"
                });
            }, __("Operations"));
        }
    }
});
