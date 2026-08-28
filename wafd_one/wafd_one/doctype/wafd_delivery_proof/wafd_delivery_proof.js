frappe.ui.form.on("WAFD Delivery Proof", {
    refresh(frm) {
        apply_proof_language(frm);
        render_delivery_photo_panel(frm);
        if (frm.is_new() || !frm.doc.project) return;
        add_guided_proof_action(frm);
        if (["مقبول بالكامل / Fully Accepted", "مقبول جزئياً / Partially Accepted"].includes(frm.doc.status)) {
            frm.add_custom_button(__("إنشاء الفاتورة / Create Invoice"), () => approve_and_invoice(frm), __("التشغيل / Operations"));
        }
    }
});

const WAFD_DELIVERY_CAPTURE_ROLES = ["System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor", "WAFD Driver"];

function render_delivery_photo_panel(frm) {
    const field = frm.fields_dict.delivery_photo_action;
    if (!field?.$wrapper) return;
    const allowed = (frappe.user_roles || []).some((role) => WAFD_DELIVERY_CAPTURE_ROLES.includes(role));
    if (!allowed) {
        field.$wrapper.empty().hide();
        return;
    }
    const photo = frm.doc.delivery_photo ? frappe.utils.escape_html(frm.doc.delivery_photo) : "";
    const uploadedBy = frm.doc.delivery_photo_uploaded_by ? frappe.utils.escape_html(frm.doc.delivery_photo_uploaded_by) : "";
    const uploadedOn = frm.doc.delivery_photo_uploaded_on ? frappe.datetime.str_to_user(frm.doc.delivery_photo_uploaded_on) : "";
    const label = frm.doc.delivery_photo ? proof_text("استبدال صورة التسليم", "Replace Delivery Photo") : proof_text("تصوير أو رفع صورة التسليم", "Capture or Upload Delivery Photo");
    field.$wrapper.show().html(`
        <div style="margin:12px 0 18px;padding:16px;border:1px solid #dfd5bf;border-radius:18px;background:#fbf8f1">
            <button type="button" class="wafd-proof-photo-button" style="width:100%;min-height:58px;border:0;border-radius:14px;background:#1d1e22;color:#fff;font-size:16px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:10px;padding:12px 16px">
                <span aria-hidden="true" style="font-size:24px">📷</span><span>${frappe.utils.escape_html(label)}</span>
            </button>
            <div style="margin-top:9px;color:#6f7075;font-size:13px">${frappe.utils.escape_html(proof_text("التقط صورة التسليم من الكاميرا أو اخترها من الجهاز.", "Capture the delivery photo or select it from the device."))}</div>
            ${photo ? `<a href="${photo}" target="_blank" rel="noopener" style="display:block;margin-top:12px"><img src="${photo}" alt="${frappe.utils.escape_html(proof_text("صورة التسليم", "Delivery Photo"))}" style="display:block;width:100%;max-height:260px;object-fit:contain;border-radius:12px;background:#fff;border:1px solid #e4ddcf"></a>` : ""}
            ${(uploadedBy || uploadedOn) ? `<div style="margin-top:9px;color:#5d5e62;font-size:12px">${frappe.utils.escape_html(proof_text("رفعها", "Uploaded by"))}: <b>${uploadedBy || "—"}</b>${uploadedOn ? ` · ${frappe.utils.escape_html(uploadedOn)}` : ""}</div>` : ""}
        </div>
    `);
    field.$wrapper.find(".wafd-proof-photo-button").on("click", () => select_and_upload_delivery_photo(frm));
}

function select_and_upload_delivery_photo(frm) {
    if (!frm.doc.delivery_trip) {
        frappe.msgprint(proof_text("اختر رحلة التوصيل أولاً.", "Select the delivery trip first."));
        return;
    }
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.setAttribute("capture", "environment");
    input.style.display = "none";
    document.body.appendChild(input);
    input.addEventListener("change", async () => {
        try {
            const file = input.files?.[0];
            if (!file) return;
            const imageData = await compress_proof_image(file);
            const response = await frappe.call({
                method: "wafd_one.driver_portal.upload_delivery_photo",
                args: {trip_name: frm.doc.delivery_trip, image_data: imageData},
                freeze: true,
                freeze_message: proof_text("جارٍ حفظ صورة التسليم...", "Saving delivery photo..."),
            });
            const result = response.message || {};
            if (!result.file_url) throw new Error(proof_text("تعذر حفظ الصورة.", "Could not save the photo."));
            await frm.set_value("delivery_photo", result.file_url);
            await frm.set_value("delivery_photo_uploaded_by", result.uploaded_by);
            await frm.set_value("delivery_photo_uploaded_on", result.uploaded_on);
            render_delivery_photo_panel(frm);
            frappe.show_alert({message: proof_text("تم حفظ صورة التسليم", "Delivery photo saved"), indicator: "green"}, 5);
        } catch (error) {
            frappe.msgprint(error.message || proof_text("تعذر رفع الصورة.", "Could not upload the photo."));
        } finally {
            input.remove();
        }
    }, {once: true});
    input.click();
}

function compress_proof_image(file, maxDimension = 1600, quality = 0.82) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = () => reject(new Error(proof_text("تعذر قراءة الصورة.", "Could not read the image.")));
        reader.onload = () => {
            const image = new Image();
            image.onerror = () => reject(new Error(proof_text("صيغة الصورة غير مدعومة.", "Unsupported image format.")));
            image.onload = () => {
                const scale = Math.min(1, maxDimension / Math.max(image.naturalWidth, image.naturalHeight));
                const canvas = document.createElement("canvas");
                canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
                canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
                canvas.getContext("2d").drawImage(image, 0, 0, canvas.width, canvas.height);
                resolve(canvas.toDataURL("image/jpeg", quality));
            };
            image.src = reader.result;
        };
        reader.readAsDataURL(file);
    });
}

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
