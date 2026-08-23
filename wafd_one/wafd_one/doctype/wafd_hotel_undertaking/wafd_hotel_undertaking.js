
// RC227: deterministic mobile Quick Entry for WAFD Hotel.
// Frappe v16 builds Quick Entry from metadata, but on iOS the generated dialog
// can collapse/clip later mandatory fields.  Use Frappe's documented custom
// QuickEntry controller hook and explicitly render the three fields needed by
// undertaking officers.
if (frappe?.ui?.form?.QuickEntryForm) {
    frappe.ui.form.WAFDHotelQuickEntryForm = class WAFDHotelQuickEntryForm extends frappe.ui.form.QuickEntryForm {
        set_meta_and_mandatory_fields() {
            this.meta = frappe.get_meta(this.doctype);
            const get_df = (fieldname, fallback) => {
                const source = (this.meta.fields || []).find((df) => df.fieldname === fieldname);
                return Object.assign({}, source || fallback);
            };
            this.docfields = [
                get_df("hotel_name_ar", {
                    fieldname: "hotel_name_ar",
                    fieldtype: "Data",
                    label: __("اسم الفندق بالعربي / Arabic Hotel Name"),
                    reqd: 1,
                }),
                get_df("hotel_name_en", {
                    fieldname: "hotel_name_en",
                    fieldtype: "Data",
                    label: __("اسم الفندق بالإنجليزي / English Hotel Name"),
                    reqd: 1,
                }),
                get_df("district", {
                    fieldname: "district",
                    fieldtype: "Data",
                    label: __("الحي / District"),
                }),
            ];
            this.docfields[0].reqd = 1;
            this.docfields[0].hidden = 0;
            this.docfields[0].read_only = 0;
            this.docfields[1].reqd = 1;
            this.docfields[1].hidden = 0;
            this.docfields[1].read_only = 0;
            this.docfields[2].hidden = 0;
            this.docfields[2].read_only = 0;
        }

        render_dialog() {
            this.hide_full_form_button = true;
            super.render_dialog();
            this.set_title(__("إضافة فندق جديد / New Hotel"));
        }
    };
}

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

async function wafd_get_undertaking_hotel_share_title(frm) {
  const hotel = (frm?.doc?.hotel || "").trim();
  if (!hotel) return "Hotel Undertaking";
  try {
    const r = await frappe.db.get_value("WAFD Hotel", hotel, ["hotel_name_en", "hotel_name"]);
    const englishName = (r?.message?.hotel_name_en || "").trim();
    if (englishName) return englishName;
    const fallbackName = (r?.message?.hotel_name || hotel || "").trim();
    return fallbackName || "Hotel Undertaking";
  } catch (_e) {
    return hotel || "Hotel Undertaking";
  }
}

async function wafd_share_generated_pdf(name, frm) {
  wafd_clear_ios_media_session();
  try {
    const blob = await wafd_fetch_generated_pdf_blob(name);
    const filename = `${name || "undertaking"}.pdf`;
    const file = new File([blob], filename, {type: "application/pdf"});
    if (navigator.share && (!navigator.canShare || navigator.canShare({files: [file]}))) {
      const hotelTitle = await wafd_get_undertaking_hotel_share_title(frm);
      await navigator.share({title: hotelTitle, files: [file]});
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
    .wafd-und-preview-overlay{position:fixed;inset:0;z-index:1060;background:#fff;display:flex;flex-direction:column;overscroll-behavior:none}
    .wafd-und-preview-head{height:54px;min-height:54px;display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid var(--border-color,#ddd);background:#fff;direction:rtl}
    .wafd-und-preview-title{font-weight:700;font-size:16px}
    .wafd-und-preview-close{border:1px solid #e5e1d7;background:#fff;width:38px;height:38px;border-radius:12px;display:grid;place-items:center;padding:0;box-shadow:0 2px 8px rgba(0,0,0,.05)}.wafd-und-preview-close svg{width:21px;height:21px;display:block}
    .wafd-und-preview-view{position:relative;flex:1;min-height:0;background:#f4f4f4;display:flex;flex-direction:column}
    .wafd-und-preview-zoom{height:42px;min-height:42px;display:flex;align-items:center;justify-content:center;gap:8px;padding:5px 8px;background:#f7f7f7;border-bottom:1px solid var(--border-color,#ddd);direction:ltr}
    .wafd-und-preview-zoom button{width:38px;height:32px;border:1px solid #d7d7d7;border-radius:9px;background:#fff;font-size:20px;line-height:1}
    .wafd-und-preview-zoom .wafd-zoom-fit{width:auto;padding:0 12px;font-size:13px;font-weight:700}
    .wafd-und-preview-zoom .wafd-zoom-label{min-width:54px;text-align:center;font-size:12px;font-weight:700;color:#555}
    .wafd-und-preview-frame{flex:1;min-height:0;width:100%;border:0;background:#f4f4f4;touch-action:auto}
    .wafd-und-preview-actions{display:flex;gap:8px;flex-wrap:wrap;padding:10px 12px calc(10px + env(safe-area-inset-bottom));border-top:1px solid var(--border-color,#ddd);background:#fff;direction:rtl}
    .wafd-und-preview-actions .btn{flex:1 1 130px;min-height:42px}
    .wafd-undertaking-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 0;direction:rtl}
    .wafd-und-assets{font-size:13px;color:var(--text-muted,#6c757d);width:100%}
    @media(max-width:767px){.wafd-und-preview-actions{gap:6px}.wafd-und-preview-actions .btn{font-size:14px}.wafd-undertaking-actions .btn{width:100%;min-height:44px}}
  `;
  document.head.appendChild(style);
}

function wafd_return_to_role_home(delay = 450) {
  setTimeout(() => {
    try { frappe.set_route("wafd-role-home"); }
    catch (_e) { window.location.assign("/desk/wafd-role-home"); }
  }, delay);
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
      <button type="button" class="wafd-und-preview-close" aria-label="${__("رجوع")}" title="${__("رجوع")}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
    </div>
    <div class="wafd-und-preview-view">
      <div class="wafd-und-preview-zoom" aria-label="${__("تكبير وتصغير المعاينة")}">
        <button type="button" class="wafd-zoom-out" aria-label="${__("تصغير")}">−</button>
        <span class="wafd-zoom-label">100%</span>
        <button type="button" class="wafd-zoom-in" aria-label="${__("تكبير")}">+</button>
        <button type="button" class="wafd-zoom-fit">${__("ملاءمة الشاشة")}</button>
      </div>
      <iframe class="wafd-und-preview-frame" sandbox="allow-same-origin" title="${__("معاينة التعهد")}"></iframe>
    </div>
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
  const zoomOutBtn = overlay.querySelector(".wafd-zoom-out");
  const zoomInBtn = overlay.querySelector(".wafd-zoom-in");
  const zoomFitBtn = overlay.querySelector(".wafd-zoom-fit");
  const zoomLabel = overlay.querySelector(".wafd-zoom-label");

  // RC207: treat the HTML undertaking as a fixed A4 page and scale the whole
  // page as one visual surface. We do NOT use CSS zoom because Safari relayouts
  // fixed/absolute elements at different rates, which caused the overlapping
  // signature/terms seen in RC205. transform:scale() preserves the exact layout.
  let previewScale = 1;
  let fitScale = 1;
  let stage = null;
  let viewport = null;
  let pinchStartDistance = 0;
  let pinchStartScale = 1;

  const distance = (touches) => {
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const applyScale = (value) => {
    if (!stage || !viewport) return;
    previewScale = Math.max(fitScale * 0.8, Math.min(4, value));
    stage.style.transform = `scale(${previewScale})`;
    viewport.style.width = `${Math.ceil(stage.__w * previewScale)}px`;
    viewport.style.height = `${Math.ceil(stage.__h * previewScale)}px`;
    if (zoomLabel) zoomLabel.textContent = `${Math.round((previewScale / Math.max(fitScale, 0.001)) * 100)}%`;
  };

  const preparePreview = () => {
    try {
      const doc = frame.contentDocument;
      if (!doc?.body || doc.body.dataset.wafdRc207Prepared) return;
      doc.body.dataset.wafdRc207Prepared = "1";
      doc.documentElement.style.overflow = "auto";
      doc.documentElement.style.webkitTextSizeAdjust = "100%";
      doc.documentElement.style.touchAction = "pan-x pan-y";
      doc.body.style.margin = "0";
      doc.body.style.padding = "0";
      doc.body.style.background = "#f3f3f3";
      doc.body.style.overflow = "visible";

      const children = Array.from(doc.body.childNodes);
      viewport = doc.createElement("div");
      viewport.id = "wafd-preview-viewport";
      viewport.style.position = "relative";
      viewport.style.margin = "12px auto 28px";
      viewport.style.overflow = "visible";

      stage = doc.createElement("div");
      stage.id = "wafd-preview-stage";
      stage.style.position = "absolute";
      stage.style.left = "0";
      stage.style.top = "0";
      stage.style.transformOrigin = "top left";
      stage.style.background = "#fff";
      stage.style.boxShadow = "0 1px 8px rgba(0,0,0,.12)";
      children.forEach((node) => stage.appendChild(node));
      viewport.appendChild(stage);
      doc.body.appendChild(viewport);

      // Measure the original page only after moving all nodes into a single stage.
      stage.style.transform = "none";
      const rect = stage.getBoundingClientRect();
      const measuredW = Math.max(stage.scrollWidth || 0, stage.offsetWidth || 0, rect.width || 0, 794);
      const measuredH = Math.max(stage.scrollHeight || 0, stage.offsetHeight || 0, rect.height || 0, 1123);
      stage.__w = measuredW;
      stage.__h = measuredH;
      stage.style.width = `${measuredW}px`;
      stage.style.minHeight = `${measuredH}px`;

      const available = Math.max(280, frame.clientWidth - 24);
      fitScale = Math.min(1, available / measuredW);
      previewScale = fitScale;
      applyScale(previewScale);

      doc.addEventListener("touchstart", (e) => {
        if (e.touches.length === 2) {
          pinchStartDistance = distance(e.touches);
          pinchStartScale = previewScale;
        }
      }, {passive:true});
      doc.addEventListener("touchmove", (e) => {
        if (e.touches.length === 2 && pinchStartDistance > 0) {
          e.preventDefault();
          applyScale(pinchStartScale * (distance(e.touches) / pinchStartDistance));
        }
      }, {passive:false});
      doc.addEventListener("touchend", (e) => {
        if (e.touches.length < 2) pinchStartDistance = 0;
      }, {passive:true});

      // Double tap resets to fit-width, useful on iPhone if pinch gestures are
      // intercepted by browser accessibility settings.
      let lastTap = 0;
      doc.addEventListener("touchend", (e) => {
        if (e.changedTouches?.length !== 1) return;
        const now = Date.now();
        if (now - lastTap < 320) applyScale(fitScale);
        lastTap = now;
      }, {passive:true});
    } catch (_e) {}
  };

  zoomOutBtn.addEventListener("click", () => applyScale(previewScale / 1.2));
  zoomInBtn.addEventListener("click", () => applyScale(previewScale * 1.2));
  zoomFitBtn.addEventListener("click", () => applyScale(fitScale));

  const reloadPreview = () => {
    stage = null;
    viewport = null;
    frame.src = `${wafd_undertaking_preview_url(currentName)}&t=${Date.now()}`;
  };
  frame.addEventListener("load", () => setTimeout(preparePreview, 120));
  reloadPreview();

  const close = () => { overlay.remove(); wafd_clear_ios_media_session(); };
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
    reloadPreview();
    wafd_clear_ios_media_session();
    saveBtn.disabled = false;
    shareBtn.disabled = false;
    issueBtn.textContent = __("تم الاعتماد والإصدار ✓");
    frappe.show_alert({message: __("تم اعتماد التعهد وإصدار PDF — اختر حفظ أو مشاركة لإتمام التعهد"), indicator: "green"}, 5);
  });
  saveBtn.addEventListener("click", async () => {
    if (!generated) return;
    await wafd_save_generated_pdf(currentName);
    close();
    wafd_return_to_role_home();
  });
  shareBtn.addEventListener("click", async () => {
    if (!generated) return;
    await wafd_share_generated_pdf(currentName, frm);
    close();
    wafd_return_to_role_home(700);
  });
}

function wafd_render_undertaking_actions(frm) {
  const id = "wafd-undertaking-direct-actions";
  frm.$wrapper.find(`#${id}`).remove();
  if (frm.is_new()) return;
  wafd_install_preview_panel_style();
  const $bar = $(`
    <div id="${id}" class="wafd-undertaking-actions" dir="rtl">
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
      {fieldname: "hotel_name", fieldtype: "Data", label: __("اسم الفندق بالعربي / Arabic Hotel Name"), reqd: 1},
      {fieldname: "hotel_name_en", fieldtype: "Data", label: __("الاسم الإنجليزي / English Name"), reqd: 1},
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

// RC221: keep a newly-created undertaking on its own Form after the first Save.
// Frappe Desk is an SPA and, on mobile, a late route change may return to the
// List after the form's after_save callback.  Timers alone were race-prone.
// Install one route listener for this DocType and activate a short-lived guard
// only after the first successful save.  The guard blocks ONLY the unwanted
// List/home fallback; normal navigation remains available immediately after
// the guard expires.
let wafd_undertaking_route_guard_installed = false;
let wafd_undertaking_route_guard = null;

function wafd_install_undertaking_route_guard() {
  if (wafd_undertaking_route_guard_installed) return;
  const router = frappe.router?.on ? frappe.router : (frappe.route?.on ? frappe.route : null);
  if (!router) return;
  wafd_undertaking_route_guard_installed = true;
  router.on("change", () => {
    const guard = wafd_undertaking_route_guard;
    if (!guard || Date.now() > guard.expires) {
      wafd_undertaking_route_guard = null;
      return;
    }
    const r = frappe.get_route?.() || [];
    const isTarget = r[0] === "Form" && r[1] === guard.doctype && r[2] === guard.name;
    if (isTarget) return;
    const isUndertakingList = r[0] === "List" && r[1] === guard.doctype;
    const isRoleHome = r[0] === "wafd-role-home" || (r[0] === "Page" && r[1] === "wafd-role-home");
    if (isUndertakingList || isRoleHome) {
      requestAnimationFrame(() => frappe.set_route("Form", guard.doctype, guard.name));
    }
  });
}

function wafd_keep_created_undertaking_open(frm) {
  if (!frm?.doc?.name || frm.is_new()) return;
  wafd_install_undertaking_route_guard();
  const target = ["Form", frm.doctype, frm.doc.name];
  wafd_undertaking_route_guard = {
    doctype: frm.doctype,
    name: frm.doc.name,
    // Long enough to cover Frappe's post-save mobile routing, short enough not
    // to interfere with the user's next intentional action.
    expires: Date.now() + 5000
  };
  const ensure = () => {
    const r = frappe.get_route?.() || [];
    if (!(r[0] === "Form" && r[1] === frm.doctype && r[2] === frm.doc.name)) {
      frappe.set_route(...target);
    }
  };
  // Immediate enforcement plus two fallbacks for slow iOS/Frappe paint cycles.
  requestAnimationFrame(ensure);
  setTimeout(ensure, 180);
  setTimeout(ensure, 900);
}

frappe.ui.form.on("WAFD Hotel Undertaking", {
  setup(frm) {
    wafd_install_undertaking_route_guard();
    frm.set_query("hotel", () => ({ query: "wafd_one.wafd_one.doctype.wafd_hotel.wafd_hotel.hotel_link_query_for_undertaking" }));
    frm.set_query("saved_beneficiary", () => ({ filters: { disabled: 0 } }));
  },
  onload(frm) {
    if (frm.is_new() && !frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS);
    if (frm.is_new() && !frm.doc.company_logo) frm.set_value("company_logo", "/assets/wafd_one/images/wafd-almadinah-official.png");
    if (frm.is_new() && frm.doc.include_signature == null) frm.set_value("include_signature", 1);
    if (frm.is_new() && frm.doc.include_stamp == null) frm.set_value("include_stamp", 1);
  },
  before_save(frm) {
    frm.__wafd_was_new_before_save = frm.is_new();
    if (!frm.doc.meal_types) frm.set_value("meal_types", WAFD_DEFAULT_MEALS);
  },
  after_save(frm) {
    if (frm.__wafd_was_new_before_save) {
      frm.__wafd_was_new_before_save = false;
      // RC222: the requested mobile flow is Save -> undertaking preview, not
      // Save -> form/list. Keep the new document route protected, then open
      // the existing full preview surface automatically so the next actions
      // are Issue, Save PDF or Share PDF without an extra navigation step.
      wafd_keep_created_undertaking_open(frm);
      if (!frm.__wafd_auto_preview_opened) {
        frm.__wafd_auto_preview_opened = true;
        setTimeout(() => {
          if (!document.querySelector(".wafd-und-preview-overlay")) {
            wafd_open_undertaking_preview(frm);
          }
        }, 220);
      }
    }
  },
  on_submit(frm) {
    // If a newly-created undertaking is submitted immediately, keep the user
    // on that same undertaking instead of falling back to the list screen.
    wafd_keep_created_undertaking_open(frm);
  },
  refresh(frm) {
    if (!wafd_is_restricted_undertaking_officer()) {
      ["company_logo", "signature_image", "company_stamp"].forEach((fieldname) => {
        if (frm.fields_dict[fieldname]) frm.set_df_property(fieldname, "hidden", 0);
      });
    }
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
  async project(frm){
    if(!frm.doc.project) return;
    const p = await frappe.db.get_doc("WAFD Catering Project", frm.doc.project);
    const values = {contract:frm.doc.contract||p.contract, mission:frm.doc.mission||p.mission, hotel:frm.doc.hotel||p.primary_hotel, beneficiary_count:frm.doc.beneficiary_count||p.beneficiary_count, start_date:frm.doc.start_date||p.start_date, end_date:frm.doc.end_date||p.end_date};
    if (p.contract) {
      const r = await frappe.db.get_value("WAFD Contract", p.contract, "contract_number");
      if (r.message?.contract_number) values.contract_number = r.message.contract_number;
    }
    await frm.set_value(values);
  },
  hotel(frm){if(!frm.doc.hotel)return;frappe.db.get_value("WAFD Hotel",frm.doc.hotel,"hotel_name").then(r=>{if(r.message?.hotel_name)frm.set_value("supply_location",r.message.hotel_name);});}
});
