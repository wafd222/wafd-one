frappe.ui.form.on("WAFD CCP Check", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.production_batch) return;
        frm.add_custom_button(__("فتح دفعة الإنتاج / Open Production Batch"), () => {
            frappe.set_route("Form", "WAFD Production Batch", frm.doc.production_batch);
        }, __("سلامة الغذاء / Food Safety"));

        if (frm.doc.compliance_status === "مطابق / Compliant") {
            frm.page.set_primary_action(__("اعتماد القياس والانتقال للتغليف / Verify & Continue to Packaging"), () => verify_and_open_packaging(frm));
        }
    },

    after_save(frm) {
        if (!frm.doc.name || frm.doc.compliance_status !== "مطابق / Compliant") return;
        verify_and_open_packaging(frm);
    }
});

async function verify_and_open_packaging(frm) {
    if (frm.__wafd_verifying) return;
    frm.__wafd_verifying = true;
    try {
        if (frm.is_dirty()) await frm.save();
        const verifyResponse = await frappe.call({
            method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.verify_ccp_and_release",
            args: { check_name: frm.doc.name },
            freeze: true,
            freeze_message: __("جارٍ التحقق من القياس والإفراج عن الدفعة...")
        });
        const verification = verifyResponse.message || {};
        if (!verification.released) return;

        const packagingResponse = await frappe.call({
            method: "wafd_one.operations.create_packaging_record",
            args: { batch_name: verification.batch_name || frm.doc.production_batch },
            freeze: true,
            freeze_message: __("جارٍ إنشاء مرحلة التغليف...")
        });
        const result = packagingResponse.message || {};
        frappe.show_alert({ message: __("تم اعتماد سلامة الغذاء — جارٍ فتح التغليف"), indicator: "green" }, 6);
        route_to_next("WAFD Packaging Record", result);
    } finally {
        frm.__wafd_verifying = false;
    }
}

function route_to_next(doctype, result) {
    if (result.name) setTimeout(() => frappe.set_route("Form", doctype, result.name), 350);
    else if (result.values) {
        frappe.route_options = result.values;
        setTimeout(() => frappe.new_doc(doctype), 350);
    }
}
