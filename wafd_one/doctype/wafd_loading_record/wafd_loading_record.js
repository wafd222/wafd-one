frappe.ui.form.on("WAFD Loading Record", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (["تم التحميل / Loaded", "خرجت / Dispatched"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Create Delivery Trip"), () => {
                frappe.call({
                    method: "wafd_one.operations.create_delivery_trip",
                    args: { loading_name: frm.doc.name },
                    freeze: true,
                    callback(r) { if (r.message?.name) frappe.set_route("Form", "WAFD Delivery Trip", r.message.name); }
                });
            }, __("Operations"));
        }
    }
});
