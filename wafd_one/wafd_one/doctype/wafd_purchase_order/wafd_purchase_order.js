frappe.ui.form.on("WAFD Purchase Order", {
    refresh(frm) {
        if (frm.is_new() || ["مسودة / Draft", "ملغي / Cancelled", "مستلم / Received"].includes(frm.doc.status)) {
            return;
        }
        frm.add_custom_button(__("Create Goods Receipt"), () => {
            frappe.call({
                method: "wafd_one.wafd_one.doctype.wafd_purchase_order.wafd_purchase_order.create_goods_receipt",
                args: { purchase_order_name: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating goods receipt..."),
                callback(r) {
                    if (r.message && r.message.name) {
                        frappe.set_route("Form", "WAFD Stock Movement", r.message.name);
                    }
                },
            });
        }, __("Actions"));
    },
});
