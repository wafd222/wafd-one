frappe.ui.form.on("WAFD Quality Inspection", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.production_batch) return;

        frm.add_custom_button(__("Open Production Batch"), () => {
            frappe.set_route("Form", "WAFD Production Batch", frm.doc.production_batch);
        }, __("Operations"));
    },

    after_save(frm) {
        if (!frm.doc.production_batch || frm.doc.result !== "ناجح / Passed") return;
        if (frm.__wafd_opening_ccp) return;
        frm.__wafd_opening_ccp = true;
        frappe.call({
            method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.prepare_ccp_check",
            args: { batch_name: frm.doc.production_batch },
            freeze: true,
            freeze_message: __("Preparing food safety measurement..."),
            callback(r) {
                const result = r.message || {};
                if (result.name) frappe.set_route("Form", "WAFD CCP Check", result.name);
                else if (result.values) frappe.new_doc("WAFD CCP Check", result.values);
            },
            always() { frm.__wafd_opening_ccp = false; }
        });
    }
});
