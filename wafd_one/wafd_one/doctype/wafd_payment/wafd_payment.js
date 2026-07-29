frappe.ui.form.on("WAFD Payment", {
    refresh(frm) {
        frm.page.clear_primary_action();
        if (frm.is_new() || frm.doc.status === "مسودة / Draft") {
            frm.page.set_primary_action(__("اعتماد التحصيل / Confirm Payment"), async () => {
                await frm.set_value("status", "معتمد / Confirmed");
                await frm.save();
                frappe.show_alert({ message: __("Payment confirmed"), indicator: "green" });
                if (frm.doc.invoice) frappe.set_route("Form", "WAFD Invoice", frm.doc.invoice);
            });
        }
    },
    invoice(frm) {
        if (!frm.doc.invoice) return;
        frappe.call({
            method: "wafd_one.finance.get_invoice_totals",
            args: { invoice_name: frm.doc.invoice },
            callback(r) {
                if (!r.message) return;
                frm.set_value("project", r.message.project);
                frm.set_value("invoice_total", r.message.invoice_total);
                frm.set_value("previously_paid", r.message.paid_amount);
                frm.set_value("outstanding_before", r.message.balance);
                if (!frm.doc.amount) frm.set_value("amount", r.message.balance);
            }
        });
    }
});
