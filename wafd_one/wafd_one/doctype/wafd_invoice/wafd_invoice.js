frappe.ui.form.on("WAFD Invoice", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.status === "ملغاة / Cancelled") return;

        if (flt(frm.doc.grand_total) <= 0) {
            frm.add_custom_button(__("Recalculate Invoice"), () => {
                frappe.call({
                    method: "wafd_one.finance.rebuild_invoice",
                    args: { invoice_name: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        if (r.message) frm.reload_doc();
                    }
                });
            }, __("Operations"));
            return;
        }

        if (flt(frm.doc.balance) > 0) {
            frm.add_custom_button(__("Register Payment"), () => {
                frappe.new_doc("WAFD Payment", {
                    invoice: frm.doc.name,
                    project: frm.doc.project,
                    invoice_total: frm.doc.grand_total,
                    previously_paid: frm.doc.paid_amount,
                    outstanding_before: frm.doc.balance,
                    payment_date: frappe.datetime.get_today(),
                    amount: frm.doc.balance,
                    status: "مسودة / Draft"
                });
            }, __("Operations"));
        }
    }
});
