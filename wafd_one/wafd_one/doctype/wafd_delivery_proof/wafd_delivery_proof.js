frappe.ui.form.on("WAFD Delivery Proof", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.project) return;
        add_guided_proof_action(frm);
        if (["مقبول بالكامل / Fully Accepted", "مقبول جزئياً / Partially Accepted"].includes(frm.doc.status)) {
            frm.add_custom_button(__("إنشاء الفاتورة / Create Invoice"), () => approve_and_invoice(frm), __("التشغيل / Operations"));
        }
    }
});

function add_guided_proof_action(frm) {
    frm.page.clear_primary_action();
    if (!["مقبول بالكامل / Fully Accepted", "مقبول جزئياً / Partially Accepted"].includes(frm.doc.status)) return;
    frm.page.set_primary_action(__("اعتماد التسليم وإنشاء الفاتورة / Approve Delivery & Create Invoice"), () => approve_and_invoice(frm));
}

async function approve_and_invoice(frm) {
    if (frm.__wafd_creating_invoice) return;
    frm.__wafd_creating_invoice = true;
    try {
        if (frm.is_dirty()) await frm.save();
        const r = await frappe.call({
            method: "wafd_one.finance.create_invoice_from_deliveries",
            args: { project_name: frm.doc.project },
            freeze: true,
            freeze_message: __("جارٍ اعتماد التسليم وإنشاء الفاتورة...")
        });
        if (r.message) {
            frappe.show_alert({ message: __("تم اعتماد التسليم — جارٍ فتح الفاتورة"), indicator: "green" }, 6);
            setTimeout(() => frappe.set_route("Form", "WAFD Invoice", r.message), 350);
        }
    } finally {
        frm.__wafd_creating_invoice = false;
    }
}
