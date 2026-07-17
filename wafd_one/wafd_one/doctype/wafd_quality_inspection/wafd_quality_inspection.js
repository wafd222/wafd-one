frappe.ui.form.on("WAFD Quality Inspection", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.production_batch) return;

        frm.add_custom_button(__("Open Production Batch"), () => {
            frappe.set_route("Form", "WAFD Production Batch", frm.doc.production_batch);
        }, __("Operations"));

        if (frm.doc.result === "ناجح / Passed") {
            frm.add_custom_button(__("Create Packaging Record"), () => {
                frappe.call({
                    method: "wafd_one.operations.create_packaging_record",
                    args: { batch_name: frm.doc.production_batch },
                    freeze: true,
                    callback(r) {
                        if (r.message?.name) frappe.set_route("Form", "WAFD Packaging Record", r.message.name);
                    }
                });
            }, __("Operations"));
        }
    }
});
