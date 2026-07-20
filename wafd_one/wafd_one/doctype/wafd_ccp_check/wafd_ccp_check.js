frappe.ui.form.on("WAFD CCP Check", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.verification_status === "تم التحقق / Verified") return;
        frm.add_custom_button(__("Verify Check"), () => {
            frm.set_value("verification_status", "تم التحقق / Verified");
            frm.save();
        }, __("Food Safety"));
    }
});
