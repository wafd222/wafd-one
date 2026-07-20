frappe.ui.form.on("WAFD Stock Movement", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.status !== "مسودة / Draft") return;
        frm.add_custom_button(__("Post Movement"), () => {
            frappe.confirm(__("Post this movement and update stock balances?"), () => {
                frappe.call({
                    method: "wafd_one.wafd_one.doctype.wafd_stock_movement.wafd_stock_movement.post_movement",
                    args: { movement_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Posting stock movement..."),
                    callback(r) {
                        if (r.message) {
                            frappe.show_alert({ message: __("Stock movement posted"), indicator: "green" });
                            frm.reload_doc();
                        }
                    }
                });
            });
        }, __("Stock"));
    }
});
