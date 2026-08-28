frappe.ui.form.on("WAFD Delivery Proof", {
    refresh(frm) {
        apply_proof_language(frm);
        if (frm.is_new() || !frm.doc.project) return;
        add_guided_proof_action(frm);
        if (["مقبول بالكامل / Fully Accepted", "مقبول جزئياً / Partially Accepted"].includes(frm.doc.status)) {
            frm.add_custom_button(__("إنشاء الفاتورة / Create Invoice"), () => approve_and_invoice(frm), __("التشغيل / Operations"));
        }
    }
});

function proof_language() {
    return localStorage.getItem("wafd_lang") || "ar";
}

function proof_text(arabic, english) {
    return proof_language() === "ar" ? arabic : english;
}

function apply_proof_language(frm) {
    const labels = {
        delivery_trip: ["رحلة التوصيل", "Delivery Trip"],
        project: ["المشروع", "Project"],
        hotel: ["الفندق", "Hotel"],
        delivery_time: ["وقت التسليم", "Delivery Time"],
        received_quantity: ["الكمية المستلمة", "Received Quantity"],
        rejected_quantity: ["الكمية المرفوضة", "Rejected Quantity"],
        receiver_name: ["اسم المستلم", "Receiver Name"],
        receiver_mobile: ["جوال المستلم", "Receiver Mobile"],
        receiver_signature: ["توقيع المستلم", "Receiver Signature"],
        delivery_photo: ["صورة التسليم", "Delivery Photo"],
        delivery_photo_uploaded_by: ["رفع صورة التسليم بواسطة", "Delivery Photo By"],
        delivery_photo_uploaded_on: ["وقت رفع صورة التسليم", "Delivery Photo Time"],
        status: ["الحالة", "Status"],
        operational_note_code: ["الملاحظة التشغيلية", "Operational Note"],
        notes_language: ["لغة الملاحظة الأصلية", "Original Note Language"],
        notes_original: ["الملاحظة الأصلية", "Original Note"],
        notes_translation_ar: ["الترجمة العربية", "Arabic Translation"],
        notes: ["الملاحظة المعروضة", "Displayed Note"],
    };
    Object.entries(labels).forEach(([fieldname, values]) => {
        if (frm.fields_dict[fieldname]) frm.set_df_property(fieldname, "label", proof_language() === "ar" ? values[0] : values[1]);
    });
}

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
