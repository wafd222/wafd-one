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

frappe.ui.form.on("WAFD Stock Movement Item", {
    ingredient(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.ingredient) {
            frappe.model.set_value(cdt, cdn, "uom", "");
            return;
        }
        frappe.db.get_value("WAFD Ingredient", row.ingredient, "uom").then((r) => {
            if (r.message && r.message.uom) {
                frappe.model.set_value(cdt, cdn, "uom", r.message.uom);
            }
        });
    },
});
