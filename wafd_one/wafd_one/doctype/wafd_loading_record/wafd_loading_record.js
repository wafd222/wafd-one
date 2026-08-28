const WAFD_LOADING_ROLES = ["System Manager", "WAFD Operations Manager", "WAFD Delivery Supervisor"];

frappe.ui.form.on("WAFD Loading Record", {
  refresh(frm) {
    if (frm.is_new()) return;
    applyLoadingLanguage(frm);
    addInlineBackAction(frm);
    const canOperate = frappe.user_roles.some((role) => WAFD_LOADING_ROLES.includes(role));
    if (canOperate) {
      renderLoadingPhotoPanel(frm);
      addGuidedLoadingAction(frm);
    } else {
      frm.fields_dict.loading_photo_action?.$wrapper?.empty().hide();
      frm.page.clear_primary_action();
    }
    frm.add_custom_button(uiText("معاينة المستند", "Preview Document"), () => openLoadingPdf(frm), uiText("المستندات", "Documents"));
    frm.add_custom_button(uiText("طباعة PDF", "Print PDF"), () => openLoadingPdf(frm), uiText("المستندات", "Documents"));
    if (canOperate && ["تم التحميل / Loaded", "خرجت / Dispatched"].includes(frm.doc.status)) {
      frm.add_custom_button(uiText("فتح رحلة التوصيل", "Open Delivery Trip"), () => {
        frappe.call({
          method: "wafd_one.operations.create_delivery_trip",
          args: {loading_name: frm.doc.name},
          freeze: true,
          callback(response) {
            if (response.message?.name) frappe.set_route("Form", "WAFD Delivery Trip", response.message.name);
          },
        });
      }, uiText("التشغيل", "Operations"));
    }
  },
});

function addInlineBackAction(frm) {
  frm.add_custom_button(uiText("رجوع", "Back"), () => {
    if (window.history.length > 1) window.history.back();
    else frappe.set_route("wafd-role-home");
  }, uiText("التنقل", "Navigation"));
}

function loadingLanguage() {
  return localStorage.getItem("wafd_lang") || "ar";
}

function uiText(arabic, english) {
  return loadingLanguage() === "ar" ? arabic : english;
}

function applyLoadingLanguage(frm) {
  const labels = {
    project: ["المشروع", "Project"], meal_plan: ["خطة الوجبة", "Meal Plan"], loading_date: ["وقت التحميل", "Loading Time"],
    quantity: ["الكمية المحملة", "Loaded Quantity"], vehicle: ["المركبة", "Vehicle"], driver: ["السائق", "Driver"],
    supervisor: ["مشرف التحميل", "Loading Supervisor"], seal_number: ["رقم الختم", "Seal Number"], loading_photo: ["صورة التحميل", "Loading Photo"],
    loading_photo_uploaded_by: ["رفع الصورة بواسطة", "Photo Uploaded By"], loading_photo_uploaded_on: ["وقت رفع الصورة", "Photo Upload Time"],
    vehicle_capacity: ["سعة المركبة", "Vehicle Capacity"], capacity_utilization_percent: ["استغلال السعة", "Capacity Utilization"],
    status: ["الحالة", "Status"], notes: ["ملاحظات", "Notes"], box_count: ["عدد الصناديق", "Box Count"],
    hot_cabinet_count: ["عدد سخانات الهوت كابن", "Hot Cabinets"], hot_cabinet_sandwich_total: ["السفندشات داخل السخانات", "Sandwiches in Hot Cabinets"],
    temperature_at_loading: ["درجة الحرارة عند التحميل", "Loading Temperature"], dispatch_time: ["وقت الخروج", "Dispatch Time"],
  };
  Object.entries(labels).forEach(([fieldname, values]) => {
    if (frm.fields_dict[fieldname]) frm.set_df_property(fieldname, "label", loadingLanguage() === "ar" ? values[0] : values[1]);
  });
  frm.set_df_property("status", "read_only", 1);
  frm.set_df_property("supervisor", "read_only", 1);
}

function renderLoadingPhotoPanel(frm) {
  const field = frm.fields_dict.loading_photo_action;
  if (!field?.$wrapper) return;
  const wrapper = field.$wrapper;
  const label = frm.doc.loading_photo ? uiText("استبدال صورة التحميل", "Replace Loading Photo") : uiText("تصوير أو رفع صورة التحميل", "Capture or Upload Loading Photo");
  const help = frm.doc.loading_photo
    ? uiText("تم توثيق الحمولة. يمكنك معاينة الصورة أو استبدالها قبل إنشاء الرحلة.", "Loading is documented. Preview or replace the photo before trip creation.")
    : uiText("صوّر الحمولة الآن قبل اعتماد التحميل وإنشاء الرحلة.", "Capture the load before approval and trip creation.");
  const photo = frm.doc.loading_photo ? frappe.utils.escape_html(frm.doc.loading_photo) : "";
  const uploadedBy = frm.doc.loading_photo_uploaded_by ? frappe.utils.escape_html(frm.doc.loading_photo_uploaded_by) : "";
  const uploadedOn = frm.doc.loading_photo_uploaded_on ? frappe.datetime.str_to_user(frm.doc.loading_photo_uploaded_on) : "";
  wrapper.show().html(`
    <div class="wafd-loading-photo-panel" style="margin:12px 0 18px;padding:16px;border:1px solid #dfd5bf;border-radius:18px;background:#fbf8f1;box-shadow:0 8px 24px rgba(41,34,22,.05)">
      <button type="button" class="wafd-loading-photo-button" style="width:100%;min-height:58px;border:0;border-radius:14px;background:#1d1e22;color:#fff;font-size:16px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:10px;padding:12px 16px">
        <span aria-hidden="true" style="font-size:24px;line-height:1">📷</span><span>${frappe.utils.escape_html(label)}</span>
      </button>
      <div style="margin-top:9px;color:#6f7075;font-size:13px;line-height:1.6">${frappe.utils.escape_html(help)}</div>
      ${photo ? `<a href="${photo}" target="_blank" rel="noopener" style="display:block;margin-top:12px"><img src="${photo}" alt="${frappe.utils.escape_html(uiText("صورة التحميل", "Loading Photo"))}" style="display:block;width:100%;max-height:260px;object-fit:contain;border-radius:12px;background:#fff;border:1px solid #e4ddcf"></a>` : ""}
      ${(uploadedBy || uploadedOn) ? `<div style="margin-top:9px;color:#5d5e62;font-size:12px">${frappe.utils.escape_html(uiText("رفعها", "Uploaded by"))}: <b>${uploadedBy || "—"}</b>${uploadedOn ? ` · ${frappe.utils.escape_html(uploadedOn)}` : ""}</div>` : ""}
    </div>
  `);
  wrapper.find(".wafd-loading-photo-button").on("click", () => selectAndUploadLoadingPhoto(frm));
}

function selectAndUploadLoadingPhoto(frm) {
  if (["خرجت / Dispatched"].includes(frm.doc.status)) {
    frappe.msgprint(uiText("لا يمكن استبدال الصورة بعد خروج الرحلة.", "The photo cannot be replaced after dispatch."));
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
      const imageData = await compressMobileImage(file);
      const response = await frappe.call({
        method: "wafd_one.driver_portal.upload_loading_photo",
        args: {loading_name: frm.doc.name, image_data: imageData},
        freeze: true,
        freeze_message: uiText("جارٍ حفظ صورة التحميل...", "Saving loading photo..."),
      });
      if (response.message?.file_url) {
        frappe.show_alert({message: uiText("تم حفظ صورة التحميل", "Loading photo saved"), indicator: "green"}, 5);
        await frm.reload_doc();
      }
    } catch (error) {
      frappe.msgprint(error.message || uiText("تعذر رفع الصورة.", "Could not upload the photo."));
    } finally {
      input.remove();
    }
  }, {once: true});
  input.click();
}

function compressMobileImage(file, maxDimension = 1600, quality = 0.82) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error(uiText("تعذر قراءة الصورة.", "Could not read the image.")));
    reader.onload = () => {
      const image = new Image();
      image.onerror = () => reject(new Error(uiText("صيغة الصورة غير مدعومة.", "Unsupported image format.")));
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

function addGuidedLoadingAction(frm) {
  frm.page.clear_primary_action();
  frm.page.set_primary_action(uiText("اعتماد وإنشاء الرحلة", "Approve & Create Trip"), async () => {
    if (frm.__wafd_transition_busy) return;
    frm.__wafd_transition_busy = true;
    try {
      if (!frm.doc.vehicle || !frm.doc.driver) {
        frappe.msgprint(uiText("اختر المركبة والسائق قبل اعتماد التحميل.", "Select the vehicle and driver before approval."));
        return;
      }
      if (!frm.doc.loading_photo) {
        frappe.msgprint(uiText("صوّر الحمولة أو ارفع صورتها قبل الاعتماد.", "Capture or upload the loading photo before approval."));
        return;
      }
      if (frm.doc.status !== "خرجت / Dispatched") await frm.set_value("status", "خرجت / Dispatched");
      if (frm.is_dirty()) await frm.save();
      const response = await frappe.call({
        method: "wafd_one.operations.create_delivery_trip",
        args: {loading_name: frm.doc.name},
        freeze: true,
        freeze_message: uiText("جارٍ اعتماد التحميل وإنشاء الرحلة...", "Approving loading and creating the trip..."),
      });
      const result = response.message || {};
      if (!result.name) frappe.throw(uiText("تعذر إنشاء أو فتح رحلة التوصيل.", "Could not create or open the delivery trip."));
      frappe.show_alert({message: uiText("تم اعتماد التحميل", "Loading approved"), indicator: "green"}, 5);
      await frappe.set_route("Form", "WAFD Delivery Trip", result.name);
    } finally {
      frm.__wafd_transition_busy = false;
    }
  });
}

async function openLoadingPdf(frm) {
  const response = await frappe.call({method: "wafd_one.document_studio.get_default_template", args: {reference_doctype: frm.doctype}});
  if (!response.message) {
    frappe.msgprint(uiText("لا يوجد قالب طباعة مفعل", "No active print template"));
    return;
  }
  const query = new URLSearchParams({template_name: response.message, doctype: frm.doctype, docname: frm.doc.name});
  window.open(`/api/method/wafd_one.document_studio.download_pdf?${query.toString()}`, "_blank");
}
