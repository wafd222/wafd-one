frappe.ui.form.on("WAFD Loading Record", {
    refresh(frm) {
        if (frm.is_new()) return;
        add_guided_loading_action(frm);
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


function add_guided_loading_action(frm) {
    frm.page.clear_primary_action();
    frm.page.set_primary_action(__("اعتماد التحميل وإنشاء رحلة التوصيل / Approve Loading & Create Trip"), async () => {
        if (!frm.doc.vehicle || !frm.doc.driver) {
            frappe.msgprint(__("اختر المركبة والسائق قبل اعتماد التحميل / Select vehicle and driver first."));
            return;
        }
        if (!frm.doc.loading_photo) {
            frappe.msgprint(__("أرفق صورة التحميل قبل الخروج / Attach loading photo before dispatch."));
            return;
        }
        await frm.set_value("status", "خرجت / Dispatched");
        await frm.save();
        frappe.call({
            method: "wafd_one.operations.create_delivery_trip",
            args: { loading_name: frm.doc.name },
            freeze: true,
            callback(r) { if (r.message?.name) frappe.set_route("Form", "WAFD Delivery Trip", r.message.name); }
        });
    });
}
