frappe.ui.form.on("WAFD Delivery Proof", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.project) return;
        if (["مقبول بالكامل / Fully Accepted", "مقبول جزئياً / Partially Accepted"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Create Invoice"), () => {
                frappe.call({
                    method: "wafd_one.finance.create_invoice_from_deliveries",
                    args: { project_name: frm.doc.project },
                    freeze: true,
                    callback(r) {
                        if (r.message) frappe.set_route("Form", "WAFD Invoice", r.message);
                    }
                });
            }, __("Operations"));
        }
    }
});
