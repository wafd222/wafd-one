const WAFD_DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner";

const WAFD_UNDERTAKING_PROTECTED_FIELDS = [
  "company_logo", "additional_terms", "authorized_signatory", "signatory_title",
  "include_signature", "include_stamp", "signature_image", "company_stamp"
];

function wafd_is_restricted_undertaking_officer() {
  const roles = new Set(frappe.user_roles || []);
  return roles.has("WAFD Undertaking Officer") &&
    !roles.has("System Manager") && !roles.has("WAFD Operations Manager");
}

function wafd_apply_undertaking_lockdown(frm) {
  if (!wafd_is_restricted_undertaking_officer()) return;
  WAFD_UNDERTAKING_PROTECTED_FIELDS.forEach((fieldname) => {
    frm.set_df_property(fieldname, "read_only", 1);
    frm.set_df_property(fieldname, "hidden", 1);
  });
  ["terms_section", "approval_section"].forEach((fieldname) => {
    if (frm.fields_dict[fieldname]) frm.set_df_property(fieldname, "hidden", 1);
  });
}

function wafd_pdf_url(file_url) {
  if (!file_url) return "";
  try { return new URL(file_url, window.location.origin).href; }
  catch (e) { return file_url; }
}

function wafd_undertaking_preview_url(name) {
  const q = new URLSearchParams({name});
  return `/api/method/wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.preview_undertaking_html?${q.toString()}`;
}

function wafd_clear_ios_media_session() {
  try {
    document.querySelectorAll("audio,video").forEach((node) => {
      try { node.pause(); node.removeAttribute("src"); node.load?.(); } catch (_e) {}
    });
    if ("mediaSession" in navigator) {
      try { navigator.mediaSession.metadata = null; } catch (_e) {}
      try { navigator.mediaSession.playbackState = "none"; } catch (_e) {}
    }
  } catch (_e) {}
}

async function wafd_fetch_generated_pdf_blob(name) {
  const response = await fetch(wafd_generated_pdf_url(name, false), {
    credentials: "same-origin",
    cache: "no-store",
    headers: {Accept: "application/pdf"}
  });
  if (!response.ok) throw new Error("PDF fetch failed");
  const source = await response.blob();
  return source.type === "application/pdf" ? source : new Blob([source], {type: "application/pdf"});
}

function wafd_generated_pdf_url(name, download=false) {
  const q = new URLSearchParams({name});
  if (download) q.set("download", "1");
  return `/api/method/wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.download_generated_pdf?${q.toString()}`;
}

async function wafd_issue_pdf(name, frm) {
  return new Promise((resolve) => {
    frappe.call({
      method: "wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.approve_and_generate_pdf",
      args: { name },
      freeze: true,
      freeze_message: __("جارٍ اعتماد التعهد وإصدار ملف PDF..."),
      callback: async (r) => {
        const result = r.message || null;
        if (result?.file_url && frm && result.docname === frm.doc.name) {
          await frm.reload_doc();
        }
        resolve(result);
      },
      error: () => resolve(null)
    });
  });
}

async function wafd_share_generated_pdf(name) {
  wafd_clear_ios_media_session();
  try {
    const blob = await wafd_fetch_generated_pdf_blob(name);
    const filename = `${name || "undertaking"}.pdf`;
    const file = new File([blob], filename, {type: "application/pdf"});
    if (navigator.share && (!navigator.canShare || navigator.canShare({files: [file]}))) {
      await navigator.share({title: __("تعهد وفد المدينة"), files: [file]});
      wafd_clear_ios_media_session();
      return;
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  } catch (e) {
    if (e?.name === "AbortError") return;
    frappe.msgprint(__("تعذر تجهيز ملف PDF للمشاركة."));
  } finally {
    wafd_clear_ios_media_session();
  }
}

async function wafd_save_generated_pdf(name) {
  wafd_clear_ios_media_session();
  try {
    const blob = await wafd_fetch_generated_pdf_blob(name);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name || "undertaking"}.pdf`;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  } catch (_e) {
    frappe.msgprint(__("تعذر حفظ ملف PDF."));
  } finally {
    wafd_clear_ios_media_session();
  }
}

function wafd_install_preview_panel_style() {
  if (document.getElementById("wafd-undertaking-preview-style")) return;
  const style = document.createElement("style");
  style.id = "wafd-undertaking-preview-style";
  style.textContent = `
    .wafd-und-preview-overlay{position:fixed;inset:0;z-index:1060;background:#fff;display:flex;flex-direction:column}
    .wafd-und-preview-head{height:54px;min-height:54px;display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid var(--border-color,#ddd);background:#fff;direction:rtl}
    .wafd-und-preview-title{font-weight:700;font-size:16px}
    .wafd-und-preview-close{border:0;background:transparent;font-size:28px;line-height:1;padding:4px 8px}
    .wafd-und-preview-frame{flex:1;width:100%;border:0;background:#f4f4f4;touch-action:manipulation}
    .wafd-und-preview-actions{display:flex;gap:8px;flex-wrap:wrap;padding:10px 12px calc(10px + env(safe-area-inset-bottom));border-top:1px solid var(--border-color,#ddd);background:#fff;direction:rtl}
    .wafd-und-preview-actions .btn{flex:1 1 130px;min-height:42px}
    .wafd-undertaking-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 0;direction:rtl}
    .wafd-und-assets{font-size:13px;color:var(--text-muted,#6c757d);width:100%}
    @media(max-width:767px){.wafd-und-preview-actions{gap:6px}.wafd-und-preview-actions .btn{font-size:14px}.wafd-undertaking-actions .btn{width:100%;min-height:44px}}
  `;
  document.head.appendChild(style);
}

function wafd_open_undertaking_preview(frm) {
  wafd_clear_ios_media_session();
  if (frm.is_new()) {
    frappe.msgprint(__("احفظ التعهد أولاً ثم افتح المعاينة."));
    return;
  }
  wafd_install_preview_panel_style();
  document.querySelector(".wafd-und-preview-overlay")?.remove();

  let currentName = frm.doc.name;
  let generated = !!frm.doc.generated_pdf;
  const overlay = document.createElement("div");
  overlay.className = "wafd-und-preview-overlay";
  overlay.innerHTML = `
    <div class="wafd-und-preview-head">
      <div class="wafd-und-preview-title">${__("معاينة التعهد")}</div>
      <button type="button" class="wafd-und-preview-close" aria-label="${__("إغلاق")}">×</button>
    </div>
    <iframe class="wafd-und-preview-frame" sandbox="allow-same-origin" title="${__("معاينة التعهد")}"></iframe>
    <div class="wafd-und-preview-actions">
      <button type="button" class="btn btn-primary wafd-preview-issue">${frm.doc.docstatus === 2 ? __("إنشاء نسخة واعتماد وإصدار") : __("اعتماد وإصدار")}</button>
      <button type="button" class="btn btn-default wafd-preview-save" ${generated ? "" : "disabled"}>${__("حفظ PDF")}</button>
      <button type="button" class="btn btn-default wafd-preview-share" ${generated ? "" : "disabled"}>${__("مشاركة PDF")}</button>
    </div>`;
  document.body.appendChild(overlay);

  const frame = overlay.querySelector(".wafd-und-preview-frame");
  const issueBtn = overlay.querySelector(".wafd-preview-issue");
  const saveBtn = overlay.querySelector(".wafd-preview-save");
  const shareBtn = overlay.querySelector(".wafd-preview-share");
  frame.src = wafd_undertaking_preview_url(currentName);

  // RC205: fit the full undertaking to the mobile viewport while preserving
  // pinch-to-zoom. The preview remains inside the same-origin HTML iframe.
  let previewZoom = 1;
  let fitZoom = 1;
  const applyPreviewZoom = (value) => {
    try {
      const doc = frame.contentDocument;
      if (!doc?.body) return;
      previewZoom = Math.max(0.25, Math.min(4, value));
      doc.documentElement.style.overflowX = "auto";
      doc.documentElement.style.webkitTextSizeAdjust = "100%";
      doc.body.style.marginInline = "auto";
      doc.body.style.zoom = String(previewZoom);
    } catch (_e) {}
  };
  const fitPreview = () => {
    try {
      const doc = frame.contentDocument;
      if (!doc?.body) return;
      doc.body.style.zoom = "1";
      const contentWidth = Math.max(
        doc.documentElement.scrollWidth || 0,
        doc.body.scrollWidth || 0,
        doc.documentElement.offsetWidth || 0,
        doc.body.offsetWidth || 0
      );
      const viewportWidth = Math.max(1, frame.clientWidth - 8);
      fitZoom = contentWidth > viewportWidth ? viewportWidth / contentWidth : 1;
      applyPreviewZoom(Math.min(1, fitZoom));

      // Pinch gesture support inside the iframe.
      let pinchStartDistance = 0;
      let pinchStartZoom = previewZoom;
      const distance = (touches) => {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
      };
      if (!doc.documentElement.dataset.wafdPinchBound) {
        doc.documentElement.dataset.wafdPinchBound = "1";
        doc.addEventListener("touchstart", (e) => {
          if (e.touches.length === 2) {
            pinchStartDistance = distance(e.touches);
            pinchStartZoom = previewZoom;
          }
        }, {passive:true});
        doc.addEventListener("touchmove", (e) => {
          if (e.touches.length === 2 && pinchStartDistance > 0) {
            const next = pinchStartZoom * (distance(e.touches) / pinchStartDistance);
            applyPreviewZoom(next);
            e.preventDefault();
          }
        }, {passive:false});
        doc.addEventListener("touchend", (e) => {
          if (e.touches.length < 2) pinchStartDistance = 0;
        }, {passive:true});
      }
    } catch (_e) {}
  };
  frame.addEventListener("load", () => setTimeout(fitPreview, 80));
  window.addEventListener("resize", fitPreview, {passive:true});

  const close = () => { overlay.remove(); window.removeEventListener("resize", fitPreview); wafd_clear_ios_media_session(); };
  overlay.querySelector(".wafd-und-preview-close").addEventListener("click", close);

  issueBtn.addEventListener("click", async () => {
    issueBtn.disabled = true;
    const oldText = issueBtn.textContent;
    issueBtn.textContent = __("جارٍ الاعتماد والإصدار...");
    const result = await wafd_issue_pdf(currentName, frm);
    if (!result?.file_url) {
      issueBtn.disabled = false;
      issueBtn.textContent = oldText;
      return;
    }
    currentName = result.docname || currentName;
    generated = true;
    frame.src = `${wafd_undertaking_preview_url(currentName)}&t=${Date.now()}`;
    wafd_clear_ios_media_session();
    saveBtn.disabled = false;
    shareBtn.disabled = false;
    issueBtn.textContent = __("تم الاعتماد والإصدار ✓");
    frappe.show_alert({message: __("تم اعتماد التعهد وإصدار PDF"), indicator: "green"}, 4);
  });
  saveBtn.addEventListener("click", async () => generated && await wafd_save_generated_pdf(currentName));
  shareBtn.addEventListener("click", () => generated && wafd_share_generated_pdf(currentName));
}

function wafd_render_undertaking_actions(frm) {
  const id = "wafd-undertaking-direct-actions";
  frm.$wrapper.find(`#${id}`).remove();
  if (frm.is_new()) return;
  wafd_install_preview_panel_style();
  const $bar = $(`
    <div id="${id}" class="wafd-undertaking-actions" dir="rtl">
      <div class="wafd-und-assets">
        <span>التوقيع: ${frm.doc.signature_image ? "محفوظ ✓" : "غير محفوظ"}</span>
        <span style="margin-inline-start:12px">الختم: ${frm.doc.company_stamp ? "محفوظ ✓" : "غير محفوظ"}</span>
      </div>
      <button type="button" class="btn btn-primary wafd-und-preview">معاينة التعهد</button>
    </div>`);
  $bar.find(".wafd-und-preview").on("click", () => wafd_open_undertaking_preview(frm));
  const $target = frm.$wrapper.find(".form-layout").first();
  if ($target.length) $target.before($bar); else frm.$wrapper.prepend($bar);
}


function wafd_add_hotel_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("إضافة فندق جديد"),
    fields: [
      {fieldname: "hotel_name", fieldtype: "Data", label: __("اسم الفندق / Hotel Name"), reqd: 1},
      {fieldname: "hotel_name_en", fieldtype: "Data", label: __("الاسم الإنجليزي / English Name")},
      {fieldname: "district", fieldtype: "Data", label: __("الحي / District")}
    ],
    primary_action_label: __("حفظ الفندق"),
    primary_action: async (values) => {
      dialog.get_primary_btn().prop("disabled", true);
      try {
        const r = await frappe.call({
          method: "wafd_one.wafd_one.doctype.wafd_hotel.wafd_hotel.create_hotel_for_undertaking",
          args: values,
          freeze: true,
          freeze_message: __("جارٍ حفظ الفندق...")
        });
        if (r.message?.name) {
          await frm.set_value("hotel", r.message.name);
          dialog.hide();
          frappe.show_alert({message: r.message.created ? __("تمت إضافة الفندق") : __("الفندق موجود وتم اختياره"), indicator: "green"}, 4);
        }
      } finally {
        dialog.get_primary_btn().prop("disabled", false);
      }
    }
  });
  dialog.show();
}

frappe.ui.form.on("WAFD Hotel Undertaking", {
  setup(frm) {
    frm.set_query("hotel", () => ({ query: "wafd_one.wafd_one.doctype.wafd_hotel.wafd_hotel.hotel_link_query_for_undertaking" }));
    frm.set_query("saved_beneficiary", () => ({ filters: { disabled: 0 } }));
  },
  onload(frm) {
    if (frm.is_new() && !frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS);
    if (frm.is_new() && !frm.doc.company_logo) frm.set_value("company_logo", "/assets/wafd_one/images/wafd-almadinah-official.png");
    if (frm.is_new() && frm.doc.include_signature == null) frm.set_value("include_signature", 1);
    if (frm.is_new() && frm.doc.include_stamp == null) frm.set_value("include_stamp", 1);
  },
  before_save(frm) { if (!frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS); },
  refresh(frm) {
    wafd_apply_undertaking_lockdown(frm);
    wafd_render_undertaking_actions(frm);
    frm.add_custom_button(__("إدارة المستفيدين المحفوظين"), () => frappe.set_route("List", "WAFD Undertaking Beneficiary"), __("المستفيدون"));
    frm.add_custom_button(__("إضافة فندق جديد"), () => wafd_add_hotel_dialog(frm));
    if (frm.is_new()) return;
    if (frm.doc.docstatus === 0) {
      frm.add_custom_button(__("تحديث البيانات المرتبطة"), () => frappe.call({
        method:"wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.load_linked_data",
        args:{name:frm.doc.name}, freeze:true, callback:()=>frm.reload_doc()
      }), __("الإجراءات"));
    }
  },
  async saved_beneficiary(frm) {
    if (!frm.doc.saved_beneficiary) return;
    const r = await frappe.call({method:"wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.get_saved_beneficiary", args:{name:frm.doc.saved_beneficiary}});
    const x=r.message||{};
    await frm.set_value({second_party_name:x.beneficiary_name||"",second_party_cr:x.identity_number||"",party_nationality:x.nationality||"",second_party_representative:x.representative_name||""});
  },
  project(frm){ if(!frm.doc.project)return; frappe.db.get_doc("WAFD Catering Project",frm.doc.project).then(p=>frm.set_value({contract:frm.doc.contract||p.contract,mission:frm.doc.mission||p.mission,hotel:frm.doc.hotel||p.primary_hotel,beneficiary_count:frm.doc.beneficiary_count||p.beneficiary_count,start_date:frm.doc.start_date||p.start_date,end_date:frm.doc.end_date||p.end_date})); },
  hotel(frm){if(!frm.doc.hotel)return;frappe.db.get_value("WAFD Hotel",frm.doc.hotel,"hotel_name").then(r=>{if(r.message?.hotel_name)frm.set_value("supply_location",r.message.hotel_name);});}
});
