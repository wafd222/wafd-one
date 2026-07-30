frappe.ui.form.on("WAFD CCP Check", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.production_batch) return;
        frm.add_custom_button(__("Open Production Batch"), () => {
            frappe.set_route("Form", "WAFD Production Batch", frm.doc.production_batch);
        }, __("Food Safety"));
    },

    after_save(frm) {
        if (!frm.doc.name || frm.doc.compliance_status !== "مطابق / Compliant") return;
        if (frm.doc.verification_status === "تم التحقق / Verified" && frm.__wafd_release_done) return;
        if (frm.__wafd_verifying) return;
        frm.__wafd_verifying = true;
        frappe.call({
            method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.verify_ccp_and_release",
            args: { check_name: frm.doc.name },
            freeze: true,
            freeze_message: __("Verifying measurement and releasing the batch..."),
            callback(r) {
                const result = r.message || {};
                if (result.released) {
                    frm.__wafd_release_done = true;
                    frappe.show_alert({ message: __("Food safety released successfully"), indicator: "green" }, 6);
                    frappe.set_route("Form", "WAFD Production Batch", result.batch_name);
                }
            },
            always() { frm.__wafd_verifying = false; }
        });
    }
});
