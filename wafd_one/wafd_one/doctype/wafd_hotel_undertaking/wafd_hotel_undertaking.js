const WAFD_DEFAULT_MEALS = "إفطار / Breakfast\nغداء / Lunch\nعشاء / Dinner";

function wafd_pdf_url(file_url) {
  if (!file_url) return "";
  try { return new URL(file_url, window.location.origin).href; }
  catch (e) { return file_url; }
}

async function wafd_get_template(frm) {
  const r = await frappe.call({
    method: "wafd_one.document_studio.get_default_template",
    args: { reference_doctype: frm.doctype }
  });
  if (!r.message) {
    frappe.msgprint(__("لا يوجد قالب تعهد مفعل"));
    return null;
  }
  return r.message;
}

async function wafd_preview_undertaking(frm) {
  const previewWindow = window.open("about:blank", "_blank");
  const template = await wafd_get_template(frm);
  if (!template) { if (previewWindow) previewWindow.close(); return; }
  const q = new URLSearchParams({template_name: template, doctype: frm.doctype, docname: frm.doc.name});
  const url = `/api/method/wafd_one.document_studio.download_pdf?${q.toString()}`;
  if (previewWindow) previewWindow.location.href = url; else window.location.href = url;
}

async function wafd_issue_pdf(frm) {
  return new Promise((resolve) => {
    frappe.call({
      method: "wafd_one.wafd_one.doctype.wafd_hotel_undertaking.wafd_hotel_undertaking.approve_and_generate_pdf",
      args: { name: frm.doc.name },
      freeze: true,
      freeze_message: __("جارٍ اعتماد التعهد وإصدار ملف PDF..."),
      callback: async (r) => {
        if (r.message?.file_url) {
          await frm.reload_doc();
          resolve(r.message);
        } else {
          resolve(null);
        }
      }
    });
  });
}

async function wafd_share_pdf(frm) {
  let fileUrl = frm.doc.generated_pdf;
  if (!fileUrl) {
    frappe.msgprint({
      title: __("ملف PDF غير موجود"),
      message: __("اعتمد التعهد وأصدر PDF أولاً، ثم استخدم زر المشاركة."),
      indicator: "orange"
    });
    return;
  }
  const url = wafd_pdf_url(fileUrl);
  try {
    const response = await fetch(url, {credentials: "same-origin"});
    if (!response.ok) throw new Error("PDF fetch failed");
    const blob = await response.blob();
    const filename = `${frm.doc.name || "undertaking"}.pdf`;
    const file = new File([blob], filename, {type: "application/pdf"});
    if (navigator.share && (!navigator.canShare || navigator.canShare({files: [file]}))) {
      await navigator.share({title: __("تعهد وفد المدينة"), files: [file]});
      return;
    }
  } catch (e) {
    if (e?.name === "AbortError") return;
  }
  window.open(url, "_blank");
}

function wafd_save_pdf(frm) {
  if (!frm.doc.generated_pdf) {
    frappe.msgprint({
      title: __("ملف PDF غير موجود"),
      message: __("اعتمد التعهد وأصدر PDF أولاً، ثم استخدم زر الحفظ."),
      indicator: "orange"
    });
    return;
  }
  const a = document.createElement("a");
  a.href = frm.doc.generated_pdf;
  a.download = `${frm.doc.name || "undertaking"}.pdf`;
  a.target = "_blank";
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function wafd_render_undertaking_actions(frm) {
  const id = "wafd-undertaking-direct-actions";
  frm.$wrapper.find(`#${id}`).remove();
  if (frm.is_new()) return;
  const hasPdf = !!frm.doc.generated_pdf;
  const canIssue = true;
  const $bar = $(
    `<div id="${id}" class="wafd-undertaking-actions" dir="rtl">
      <div class="wafd-und-assets">
        <span class="${frm.doc.signature_image ? "is-ready" : "is-missing"}">التوقيع: ${frm.doc.signature_image ? "محفوظ ✓" : "غير محفوظ"}</span>
        <span class="${frm.doc.company_stamp ? "is-ready" : "is-missing"}">الختم: ${frm.doc.company_stamp ? "محفوظ ✓" : "غير محفوظ"}</span>
      </div>
      <button type="button" class="btn btn-default wafd-und-preview">معاينة التعهد</button>
      <button type="button" class="btn btn-primary wafd-und-issue">${frm.doc.docstatus === 2 ? "إنشاء نسخة واعتماد وإصدار PDF" : "اعتماد وإصدار PDF"}</button>
      <button type="button" class="btn btn-default wafd-und-share" ${hasPdf ? "" : "disabled"}>مشاركة PDF</button>
      <button type="button" class="btn btn-default wafd-und-save" ${hasPdf ? "" : "disabled"}>حفظ PDF</button>
    </div>`
  );
  $bar.find(".wafd-und-preview").on("click", () => wafd_preview_undertaking(frm));
  $bar.find(".wafd-und-issue").on("click", async () => {
    const pdfWindow = window.open("about:blank", "_blank");
    const result = await wafd_issue_pdf(frm);
    if (result?.file_url) {
      if (result.created_from_cancelled && result.docname) {
        frappe.show_alert({message: __("تم إنشاء نسخة جديدة من التعهد الملغي وإصدارها"), indicator: "green"}, 5);
      }
      if (pdfWindow) pdfWindow.location.href = result.file_url; else window.location.href = result.file_url;
    } else if (pdfWindow) pdfWindow.close();
  });
  $bar.find(".wafd-und-share").on("click", () => wafd_share_pdf(frm));
  $bar.find(".wafd-und-save").on("click", () => wafd_save_pdf(frm));

  const $target = frm.$wrapper.find(".form-layout").first();
  if ($target.length) $target.before($bar); else frm.$wrapper.prepend($bar);
}

frappe.ui.form.on("WAFD Hotel Undertaking", {
  setup(frm) {
    frm.set_query("hotel", () => ({ query: "wafd_one.wafd_one.doctype.wafd_hotel.wafd_hotel.hotel_link_query" }));
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
    wafd_render_undertaking_actions(frm);
    frm.add_custom_button(__("إدارة المستفيدين المحفوظين"), () => frappe.set_route("List", "WAFD Undertaking Beneficiary"), __("المستفيدون"));
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
