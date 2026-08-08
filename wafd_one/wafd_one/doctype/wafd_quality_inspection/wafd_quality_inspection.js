frappe.ui.form.on("WAFD Quality Inspection", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.production_batch) return;

        frm.add_custom_button(__("فتح دفعة الإنتاج / Open Production Batch"), () => {
            frappe.set_route("Form", "WAFD Production Batch", frm.doc.production_batch);
        }, __("التشغيل / Operations"));

        if (frm.doc.result === "ناجح / Passed") {
            frm.page.set_primary_action(__("اعتماد الجودة والمتابعة لسلامة الغذاء / Approve & Continue"), () => continue_to_ccp(frm));
        }
    },

    after_save(frm) {
        if (!frm.doc.production_batch || frm.doc.result !== "ناجح / Passed") return;
        continue_to_ccp(frm);
    }
});

async function continue_to_ccp(frm) {
    if (frm.__wafd_opening_ccp) return;
    frm.__wafd_opening_ccp = true;
    try {
        if (frm.is_dirty()) await frm.save();
        const r = await frappe.call({
            method: "wafd_one.wafd_one.doctype.wafd_production_batch.wafd_production_batch.prepare_ccp_check",
            args: { batch_name: frm.doc.production_batch },
            freeze: true,
            freeze_message: __("جارٍ اعتماد الجودة وتجهيز قياس سلامة الغذاء...")
        });
        const result = r.message || {};
        frappe.show_alert({ message: __("تم اعتماد الجودة — جارٍ فتح قياس سلامة الغذاء"), indicator: "green" }, 5);
        if (result.name) {
            setTimeout(() => frappe.set_route("Form", "WAFD CCP Check", result.name), 350);
        } else if (result.values) {
            frappe.route_options = result.values;
            setTimeout(() => frappe.new_doc("WAFD CCP Check"), 350);
        }
    } finally {
        frm.__wafd_opening_ccp = false;
    }
}
