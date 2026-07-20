frappe.ui.form.on("WAFD Payment", {
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
