frappe.ui.form.on("WAFD Packaging Record", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (frm.doc.status === "مكتمل / Completed") {
            frm.add_custom_button(__("Create Loading Record"), () => {
                frappe.call({
                    method: "wafd_one.operations.create_loading_record",
                    args: { packaging_name: frm.doc.name },
                    freeze: true,
                    callback(r) { if (r.message?.name) frappe.set_route("Form", "WAFD Loading Record", r.message.name); }
                });
            }, __("Operations"));
        }
    }
});
