frappe.pages["wafd-iftar-team"].on_page_load = function (wrapper) {
  document.body.classList.add("wafd-at-iftar-team");
  $(wrapper).addClass("wafd-iftar-team-page");
  const page = frappe.ui.make_app_page({ parent: wrapper, title: __("متابعة وتشغيل إفطار الصائم"), single_column: true });
  const $root = $('<div class="ift-simple"></div>').appendTo(page.body);
  wrapper.__iftar_rc314 = { page, $root, loading: false, data: null };
  window.__wafdIftarTeamWrapper = wrapper;
};

frappe.pages["wafd-iftar-team"].on_page_show = function (wrapper) {
  window.__wafdIftarTeamWrapper = wrapper;
  window.wafdIftarStageLoad?.(wrapper);
};

(function () {
  const API = "wafd_one.wafd_one.iftar_stage_portal.";
  const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
  const fmtDate = (v) => v ? frappe.datetime.str_to_user(String(v)) : "—";
  const fmtTime = (v) => v ? frappe.datetime.str_to_user(String(v)) : "—";
  const num = (v) => Number(v || 0).toLocaleString("en-US");

  async function call(method, args = {}) {
    const r = await frappe.call({ method: API + method, args, freeze: false });
    return r.message;
  }

  function stageLabel(key) {
    return ({ production:"الإنتاج", packaging:"التغليف", loading:"التحميل", delivery_plan:"توزيع السيارات", in_transit:"في الطريق", delivered:"التسليم" })[key] || "مكتمل";
  }

  function header(data) {
    const modeText = ({
      management: "الإدارة · متابعة المشاريع وإسناد الفريق",
      project_manager: "مدير المشروع · متابعة مراحل التنفيذ",
      kitchen: "مشرف المطبخ · الإنتاج والتغليف والتحميل",
      delivery: "مشرف التوصيل · توزيع السيارات ومتابعة التسليم",
      site: "مدير الموقع · الاستلام ومتابعة المشرفين",
      supervisor: "مشرف السفر · الاستلام والتوزيع والتوثيق",
      viewer: "متابعة الجهة الخارجية · قراءة فقط"
    })[data.mode] || "إفطار الصائم";
    return `<div class="ift-head">
      <div><span class="ift-kicker">WAFD ONE · IFTAR SAIM</span><h1>إفطار الصائم</h1><p>${esc(modeText)}</p></div>
      <div class="ift-live"><span class="ift-live-dot"></span><b>${esc(data.full_name || data.user || "")}</b></div>
    </div>`;
  }

  function emptyState(text) {
    return `<div class="ift-empty"><span>✓</span><h2>${esc(text)}</h2><p>ستظهر المهمة تلقائياً عندما تصبح جاهزة.</p></div>`;
  }

  function projectIdentity(p) {
    return `<div class="ift-card-top"><span class="ift-state ${p.current_operation?.current_stage === 'complete' ? 'done' : 'working'}">${p.current_operation ? stageLabel(p.current_operation.current_stage) : 'المشروع'}</span><small>${esc(p.name)}</small></div>
      <h3>${esc(p.project_title || p.distribution_site || p.name)}</h3>
      <p>${esc(p.contracting_entity || "—")} · ${esc(p.distribution_site || "—")}</p>`;
  }

  function componentsBlock(p) {
    const comps = (p.components || []).map(x => `<span>${esc(x.name)}${x.quantity_per_meal ? ` · ${esc(x.quantity_per_meal)} ${esc(x.uom || '')}` : ''}</span>`).join("");
    const adds = (p.additions || []).map(x => `<span class="addon">+ ${esc(x.name)}${x.notes ? ` · ${esc(x.notes)}` : ''}</span>`).join("");
    return `<div class="ift-meal-box"><b>محتويات الوجبة</b><div class="ift-chips">${comps || '<span>حسب المشروع المعتمد</span>'}</div>${adds ? `<b class="ift-addon-title">الإضافات</b><div class="ift-chips">${adds}</div>` : ''}</div>`;
  }

  function workflowNotes(text) {
    if (!text) return "";
    const lines = String(text).split(/\n+/).filter(Boolean).map(x => `<div>${esc(x)}</div>`).join("");
    return `<div class="ift-notes"><b>ملاحظات التشغيل</b>${lines}</div>`;
  }

  function kitchenCard(p) {
    const o = p.task;
    if (!o) return `<div class="ift-task-card completed">${projectIdentity(p)}<div class="ift-complete-icon">✓</div><div class="ift-success">تم إكمال جميع أيام المشروع في المطبخ.</div></div>`;
    const planned = Number(o.planned_meals || 0);
    const prod = Number(o.produced_meals || 0) >= planned && planned > 0;
    const pack = prod && Number(o.packaged_meals || 0) >= planned;
    const load = pack && Number(o.loaded_meals || 0) >= planned;
    return `<div class="ift-task-card focus" data-project="${esc(p.name)}" data-operation="${esc(o.name)}">
      ${projectIdentity(p)}
      <div class="ift-day-banner"><div><span>اليوم التشغيلي</span><b>${num(o.day_index)} من ${num(o.day_total)}</b></div><div><span>التاريخ</span><b>${fmtDate(o.operation_date)}</b></div></div>
      <div class="ift-big-number"><b>${num(o.planned_meals)}</b><span>وجبة مطلوبة اليوم</span></div>
      ${componentsBlock(p)}
      ${workflowNotes(o.display_notes)}
      <div class="ift-stage-buttons">
        ${stageButton("production", "اعتماد الإنتاج", prod, !prod, prod ? "تم الإنتاج" : "اعتماد عدد اليوم كمنتج")}
        ${stageButton("packaging", "اعتماد التغليف", pack, prod && !pack, pack ? "تم التغليف" : "يُفتح بعد اعتماد الإنتاج")}
        ${stageButton("loading", "اعتماد التحميل", load, pack && !load, load ? "تم التحميل" : "يُفتح بعد اعتماد التغليف")}
      </div>
    </div>`;
  }

  function stageButton(stage, label, done, enabled, hint) {
    return `<button type="button" class="ift-stage-btn ${done ? 'done' : ''}" data-stage="${stage}" ${enabled ? '' : 'disabled'}>
      <span class="ift-stage-icon">${done ? '✓' : '○'}</span><span><b>${esc(label)}</b><small>${esc(hint)}</small></span>
    </button>`;
  }

  function tripRows(trips) {
    if (!trips || !trips.length) return "";
    return `<div class="ift-trip-list">${trips.map(t => `<div><span><b>${esc(t.vehicle_label || t.vehicle || 'سيارة')}</b><small>${esc(t.driver_label || t.driver || '')}</small></span><span><b>${num(t.quantity)} وجبة</b><small>${esc(t.status || '')}</small></span></div>`).join('')}</div>`;
  }

  function deliveryTask(p, o) {
    return `<div class="ift-task-card focus" data-project="${esc(p.name)}" data-operation="${esc(o.name)}">
      ${projectIdentity(p)}
      <div class="ift-day-banner"><div><span>اليوم التشغيلي</span><b>${num(o.day_index)} من ${num(o.day_total)}</b></div><div><span>التاريخ</span><b>${fmtDate(o.operation_date)}</b></div></div>
      <div class="ift-numbers four"><div><b>${num(o.loaded_meals)}</b><span>وجبة جاهزة</span></div><div><b>${num(o.cartons)}</b><span>كرتون</span></div><div><b>${num(p.max_carton_capacity || 25)}</b><span>وجبة/كرتون</span></div><div><b>${num(o.day_index)}</b><span>اليوم</span></div></div>
      ${workflowNotes(o.display_notes)}
      <button type="button" class="btn btn-dark ift-primary ift-open-allocation">توزيع الوجبات على السيارات واعتماد الخطة</button>
    </div>`;
  }

  function deliveryTracking(p, o) {
    return `<div class="ift-project-card"><div class="ift-card-top"><span class="ift-state working">متابعة التوصيل</span><small>${fmtDate(o.operation_date)}</small></div>
      <h3>${esc(p.project_title || p.distribution_site || p.name)}</h3><p>${esc(p.distribution_site || '')}</p>
      <div class="ift-simple-progress"><i style="width:${Number(o.progress_percent || 0)}%"></i></div>
      <div class="ift-summary-line"><span>المرحلة الحالية</span><b>${esc(stageLabel(o.current_stage))}</b></div>
      ${tripRows(o.trips)}${workflowNotes(o.display_notes)}</div>`;
  }

  function monitorCard(p, canAssign, externalView) {
    const o = p.current_operation;
    const stages = o?.stages || [];
    return `<div class="ift-project-card admin-project" data-project="${esc(p.name)}">
      ${projectIdentity(p)}
      <div class="ift-numbers four"><div><b>${num(p.daily_meals)}</b><span>وجبة يومياً</span></div><div><b>${num(p.cartons_per_day)}</b><span>كرتون يومياً</span></div><div><b>${num(p.number_of_days)}</b><span>يوم تشغيل</span></div><div><b>${o ? num(o.progress_percent) + '%' : '—'}</b><span>إنجاز اليوم</span></div></div>
      ${o ? `<div class="ift-monitor-day"><span>اليوم ${num(o.day_index)} من ${num(o.day_total)}</span><b>${fmtDate(o.operation_date)}</b></div>` : ''}
      <div class="ift-stage-strip">${stages.map(s => `<span class="${s.done ? 'done' : ''}">${s.done ? '✓ ' : ''}${esc(s.label)}</span>`).join('')}</div>
      ${(!externalView && o) ? tripRows(o.trips) + workflowNotes(o.display_notes) : ''}
      ${!externalView ? `<div class="ift-team-summary"><span><b>مدير المشروع</b>${esc(p.project_manager_user || 'غير مسند')}</span><span><b>مشرف المطبخ</b>${esc(p.kitchen_supervisor_user || 'غير مسند')}</span><span><b>مشرف التوصيل</b>${esc(p.delivery_supervisor_user || 'غير مسند')}</span><span><b>المتابع الخارجي</b>${esc(p.external_viewer_user || 'غير مسند')}</span></div>` : '<div class="ift-success">متابعة للقراءة فقط — لا يمكن تعديل أو اعتماد أي مرحلة.</div>'}
      ${canAssign ? '<div class="ift-actions"><button class="btn btn-default ift-assign-team">إسناد شاشات المشروع</button><button class="btn btn-default ift-open-legacy">فتح إدارة إفطار الصائم</button></div>' : ''}
    </div>`;
  }

  function reportInbox(data) {
    const rows = data.report_inbox || [];
    if (!rows.length) return `<div class="ift-section-title"><h2>التقارير اليومية</h2><span>0</span></div>${emptyState("لا توجد تقارير معتمدة من مدير الموقع حتى الآن")}`;
    return `<div class="ift-section-title"><h2>التقارير اليومية للإدارة</h2><span>${rows.length}</span></div><div class="ift-report-inbox">${rows.map(r => `<div class="ift-report-inbox-card" data-operation="${esc(r.name)}">
      <div class="ift-card-top"><span class="ift-state ${r.administration_report_approved ? 'done' : 'working'}">${r.administration_report_approved ? 'معتمد من الإدارة' : 'بانتظار اعتماد الإدارة'}</span><small>${esc(fmtDate(r.operation_date))}</small></div>
      <h3>${esc(r.project_title || r.project)}</h3><p>${esc(r.distribution_site || '')} · ${esc(r.contracting_entity || '')}</p>
      <div class="ift-numbers four"><div><b>${num(r.planned_meals)}</b><span>المخطط</span></div><div><b>${num(r.received_meals)}</b><span>المستلم</span></div><div><b>${num(r.supervisor_count)}</b><span>المشرفون</span></div><div><b>${num(Number(r.surplus_meals||0)+Number(r.preservation_society_quantity||0)+Number(r.waste_meals||0))}</b><span>الفائض والمعالجة</span></div></div>
      <div class="ift-report-status">${r.administration_report_approved ? `✓ اعتمدته الإدارة ${esc(fmtTime(r.administration_report_approved_at))}` : `✓ اعتمده مدير الموقع ${esc(fmtTime(r.site_report_approved_at))}`}</div>
      <div class="ift-actions"><button class="btn btn-default ift-open-official-report">معاينة التقرير الرسمي</button>${data.mode === 'management' && !r.administration_report_approved ? '<button class="btn btn-dark ift-admin-approve-report">اعتماد الإدارة وإرساله للرئاسة</button>' : ''}</div>
    </div>`).join('')}</div>`;
  }

  function officialReportUrls(operation) {
    const params = new URLSearchParams({doctype:"WAFD Iftar Daily Operation",name:operation,format:"WAFD Iftar Official Daily Report",no_letterhead:"1"});
    return {preview:`/printview?${params.toString()}`,pdf:`/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`};
  }

  function downloadReportBlob(blob, filename) {
    const href=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=href;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),1200);
  }

  function openOfficialReportPreview(operation) {
    const urls=officialReportUrls(operation),filename=`${operation}-official-report.pdf`;
    $(".ift-official-preview").remove();
    const $screen=$(`<div class="ift-official-preview" dir="rtl"><div class="ift-official-toolbar"><button type="button" class="back" data-report-back>‹ <span>رجوع</span></button><div class="identity"><b>التقرير اليومي الرسمي</b><small>شركة وفد المدينة لخدمات الإعاشة</small></div><button type="button" data-report-share disabled>⇧ <span>مشاركة</span></button><button type="button" data-report-print>⌑ <span>طباعة</span></button><button type="button" data-report-download>↓ <span>تنزيل PDF</span></button></div><div class="ift-official-frame-wrap"><iframe title="معاينة التقرير الرسمي" src="${esc(urls.preview)}"></iframe></div></div>`).appendTo(document.body);
    const frame=$screen.find("iframe")[0];
    const $share=$screen.find("[data-report-share]");let cachedPdf=null,pdfFailure=null;
    const pdfReady=fetch(urls.pdf,{credentials:"same-origin"}).then(response=>{if(!response.ok)throw new Error("تعذر إنشاء ملف PDF");return response.blob()}).then(blob=>{cachedPdf=blob;$share.prop("disabled",false);return blob}).catch(error=>{pdfFailure=error;$share.prop("disabled",false);return null});
    const fetchPdf=async()=>cachedPdf||(await pdfReady)||Promise.reject(pdfFailure||new Error("تعذر إنشاء ملف PDF"));
    $screen.on("click","[data-report-back]",()=>$screen.remove());
    $screen.on("click","[data-report-download]",async()=>{try{downloadReportBlob(await fetchPdf(),filename)}catch(e){frappe.msgprint(e.message||"تعذر تنزيل التقرير")}});
    $screen.on("click","[data-report-print]",()=>{try{frame.contentWindow.focus();frame.contentWindow.print()}catch(_e){window.open(urls.pdf,"_blank","noopener")}});
    $screen.on("click","[data-report-share]",()=>{try{const absolutePdf=new URL(urls.pdf,window.location.origin).href;if(cachedPdf&&typeof File!=="undefined"){const file=new File([cachedPdf],filename,{type:"application/pdf"});if(navigator.share&&(!navigator.canShare||navigator.canShare({files:[file]}))){navigator.share({title:"التقرير اليومي الرسمي لمشروع إفطار الصائم",files:[file]}).catch(e=>{if(e?.name!=="AbortError")downloadReportBlob(cachedPdf,filename)});return}}if(navigator.share){navigator.share({title:"التقرير اليومي الرسمي لمشروع إفطار الصائم",url:absolutePdf}).catch(e=>{if(e?.name!=="AbortError"&&cachedPdf)downloadReportBlob(cachedPdf,filename)});return}if(cachedPdf){downloadReportBlob(cachedPdf,filename);return}window.open(urls.pdf,"_blank","noopener")}catch(e){frappe.msgprint(e.message||"تعذرت مشاركة التقرير")}});
  }

  function render(wrapper, data) {
    const state = wrapper.__iftar_rc314;
    state.data = data;
    let content = "";
    if (data.mode === "kitchen") {
      const cards = (data.projects || []).map(kitchenCard).join("");
      content = `<div class="ift-section-title"><h2>مهمة المطبخ</h2><span>${(data.projects || []).length}</span></div>${cards || emptyState("لا توجد مهمة مطبخ مسندة الآن")}`;
    } else if (data.mode === "delivery") {
      let pending = "", tracking = "";
      (data.projects || []).forEach(p => {
        pending += (p.pending_tasks || []).map(o => deliveryTask(p,o)).join("");
        tracking += (p.tracking || []).map(o => deliveryTracking(p,o)).join("");
      });
      content = `<div class="ift-section-title"><h2>جاهز للتوزيع</h2></div>${pending || emptyState("لا توجد كميات جاهزة للتوزيع الآن")}
        ${tracking ? `<div class="ift-section-title"><h2>قيد التوصيل</h2></div><div class="ift-project-list">${tracking}</div>` : ''}`;
    } else {
      const readOnly = data.mode === "viewer";
      const title = readOnly ? "متابعة المشروع" : "متابعة مراحل المشاريع";
      content = `<div class="ift-section-title"><h2>${title}</h2><span>${(data.projects || []).length}</span></div><div class="ift-project-list">${(data.projects || []).map(p => monitorCard(p, data.can_manage_team, readOnly)).join('')}</div>`;
      if (!(data.projects || []).length) content += emptyState(readOnly ? "لا يوجد مشروع مسند لحساب المتابعة" : "لا توجد مشاريع ظاهرة لهذا الحساب");
      if (data.mode === "management" || data.mode === "project_manager") content += reportInbox(data);
    }
    state.$root.html(header(data) + `<div class="ift-content">${content}</div>`);
    bindEvents(wrapper);
  }

  function bindEvents(wrapper) {
    const $root = wrapper.__iftar_rc314.$root;
    $root.off(".rc314");
    $root.on("click.rc314", ".ift-stage-btn:not(:disabled)", async function () {
      const $card = $(this).closest("[data-operation]");
      const operation = $card.data("operation");
      const stage = $(this).data("stage");
      const label = stageLabel(stage);
      const d = new frappe.ui.Dialog({ title: `اعتماد ${label}`, fields:[{fieldname:"note",fieldtype:"Small Text",label:"ملاحظة (اختياري)"}], primary_action_label:"اعتماد المرحلة", primary_action: async values => {
        d.get_primary_btn().prop("disabled", true);
        try { await call("approve_kitchen_stage", { operation_name:operation, stage, note:values.note || "" }); d.hide(); frappe.show_alert({message:`تم اعتماد ${label}`,indicator:"green"}); await window.wafdIftarStageLoad(wrapper); }
        catch(e){ d.get_primary_btn().prop("disabled", false); throw e; }
      }}); d.show();
    });

    $root.on("click.rc314", ".ift-open-allocation", function () {
      const $card = $(this).closest("[data-operation]");
      openAllocationDialog(wrapper, String($card.data("operation")));
    });

    $root.on("click.rc314", ".ift-assign-team", function () {
      const projectName = String($(this).closest("[data-project]").data("project"));
      openTeamDialog(wrapper, projectName);
    });
    $root.on("click.rc314", ".ift-open-legacy", function () { frappe.set_route("wafd-iftar-operations"); });
    $root.on("click.rc314", ".ift-open-official-report", function () {
      const operation = String($(this).closest("[data-operation]").data("operation"));
      openOfficialReportPreview(operation);
    });
    $root.on("click.rc314", ".ift-admin-approve-report", function () {
      const operation = String($(this).closest("[data-operation]").data("operation"));
      const d = new frappe.ui.Dialog({title:"اعتماد الإدارة والتقرير النهائي",fields:[
        {fieldname:"recipient",fieldtype:"Data",label:"الجهة المستلمة",default:"رئاسة شؤون الحرمين",reqd:1},
        {fieldname:"administration_signature",fieldtype:"Signature",label:"توقيع الإدارة",reqd:1},
        {fieldname:"administration_stamp",fieldtype:"Attach Image",label:"ختم الإدارة",reqd:1},
        {fieldname:"administration_notes",fieldtype:"Small Text",label:"ملاحظات الإدارة"}
      ],primary_action_label:"اعتماد وإرسال للرئاسة",primary_action:async values=>{
        d.get_primary_btn().prop("disabled",true);
        try{
          await frappe.call({method:"wafd_one.wafd_one.iftar_team.send_authority_report",args:{operation_name:operation,...values},freeze:true,freeze_message:"جاري اعتماد التقرير النهائي..."});
          d.hide();frappe.show_alert({message:"تم اعتماد الإدارة وأصبح تقرير PDF جاهزاً للرئاسة",indicator:"green"});await window.wafdIftarStageLoad(wrapper);
        }catch(e){d.get_primary_btn().prop("disabled",false);throw e;}
      }});d.show();
    });
  }

  function openTeamDialog(wrapper, projectName) {
    const data = wrapper.__iftar_rc314.data;
    const p = (data.projects || []).find(x => x.name === projectName);
    const d = new frappe.ui.Dialog({ title:"إسناد شاشات مشروع إفطار الصائم", fields:[
      {fieldname:"project_manager_user",fieldtype:"Link",options:"User",label:"مدير المشروع",default:p.project_manager_user || ""},
      {fieldname:"kitchen_supervisor_user",fieldtype:"Link",options:"User",label:"مشرف المطبخ",default:p.kitchen_supervisor_user || ""},
      {fieldname:"delivery_supervisor_user",fieldtype:"Link",options:"User",label:"مشرف التوصيل",default:p.delivery_supervisor_user || ""},
      {fieldname:"site_manager_user",fieldtype:"Link",options:"User",label:"مدير موقع إفطار الصائم",default:p.site_manager_user || ""},
      {fieldname:"external_viewer_user",fieldtype:"Link",options:"User",label:"الطرف الخارجي (قراءة فقط)",default:p.external_viewer_user || ""}
    ], primary_action_label:"حفظ الإسناد", primary_action: async values => {
      d.get_primary_btn().prop("disabled", true);
      try { await call("save_project_team", {project_name:projectName, ...values}); d.hide(); frappe.show_alert({message:"تم حفظ الإسناد",indicator:"green"}); await window.wafdIftarStageLoad(wrapper); }
      catch(e){ d.get_primary_btn().prop("disabled", false); throw e; }
    }}); d.show();
  }

  function openAllocationDialog(wrapper, operationName) {
    const data = wrapper.__iftar_rc314.data;
    const p = (data.projects || []).find(x => (x.pending_tasks || []).some(o => o.name === operationName));
    const o = p && (p.pending_tasks || []).find(x => x.name === operationName);
    if (!p || !o) return;
    const vehicles = data.vehicles || [], drivers = data.drivers || [];
    const vopts = vehicles.map(v => `<option value="${esc(v.name)}">${esc(v.plate_number || v.name)}${v.capacity_meals ? ` · سعة ${num(v.capacity_meals)}` : ''}</option>`).join('');
    const dopts = drivers.map(v => `<option value="${esc(v.name)}">${esc(v.driver_name || v.name)}</option>`).join('');
    const d = new frappe.ui.Dialog({ title:`توزيع ${num(o.loaded_meals)} وجبة · ${num(o.cartons)} كرتون`, size:"large", fields:[{fieldname:"html",fieldtype:"HTML"},{fieldname:"note",fieldtype:"Small Text",label:"ملاحظات عامة تنتقل حتى التسليم"}], primary_action_label:"اعتماد توزيع السيارات", primary_action: async values => {
      const rows = [];
      d.$wrapper.find(".ift-alloc-row").each(function(){ const $r=$(this); const q=Number($r.find(".qty").val()||0); if($r.find(".vehicle").val() || $r.find(".driver").val() || q){ rows.push({vehicle:$r.find(".vehicle").val(),driver:$r.find(".driver").val(),quantity:q,note:$r.find(".row-note").val()||""}); }});
      d.get_primary_btn().prop("disabled", true);
      try { await call("approve_delivery_plan", {operation_name:operationName, allocations:rows, note:values.note || ""}); d.hide(); frappe.show_alert({message:"تم اعتماد خطة التوصيل وإرسال الرحلات للسائقين",indicator:"green"}); await window.wafdIftarStageLoad(wrapper); }
      catch(e){ d.get_primary_btn().prop("disabled", false); throw e; }
    }});
    d.show();
    const $h = d.fields_dict.html.$wrapper;
    $h.html(`<div class="ift-allocation"><div class="ift-allocation-summary"><b>${num(o.loaded_meals)} وجبة</b><span>${num(o.cartons)} كرتون · ${esc(p.distribution_site || '')}</span></div><div class="ift-alloc-rows"></div><button type="button" class="btn btn-default ift-add-vehicle">+ إضافة سيارة</button><div class="ift-allocation-total">الموزع: <b>0</b> / ${num(o.loaded_meals)} وجبة</div></div>`);
    const add = () => {
      $h.find(".ift-alloc-rows").append(`<div class="ift-alloc-row"><select class="form-control vehicle"><option value="">اختر السيارة</option>${vopts}</select><select class="form-control driver"><option value="">اختر السائق</option>${dopts}</select><input class="form-control qty" type="number" min="1" placeholder="عدد الوجبات"><input class="form-control row-note" type="text" placeholder="ملاحظة السيارة (اختياري)"><button type="button" class="btn btn-default remove">×</button></div>`);
    };
    const total = () => { let s=0; $h.find(".qty").each(function(){s += Number($(this).val()||0);}); $h.find(".ift-allocation-total b").text(num(s)); $h.find(".ift-allocation-total").toggleClass("ok", s === Number(o.loaded_meals||0)); };
    add(); $h.on("click", ".ift-add-vehicle", add); $h.on("click", ".remove", function(){ $(this).closest(".ift-alloc-row").remove(); total(); }); $h.on("input change", ".qty", total);
  }

  window.wafdIftarStageLoad = async function (wrapper) {
    const state = wrapper.__iftar_rc314;
    if (!state || state.loading) return;
    state.loading = true;
    state.$root.html('<div class="ift-loading">جاري تحميل مهام إفطار الصائم…</div>');
    try { render(wrapper, await call("get_portal_data")); }
    catch (e) { state.$root.html(`<div class="ift-empty"><span>!</span><h2>تعذر تحميل الشاشة</h2><p>${esc(e.message || e)}</p></div>`); }
    finally { state.loading = false; }
  };

  frappe.realtime.on("wafd_iftar_stage_assignment", () => {
    const wrapper = window.__wafdIftarTeamWrapper;
    if (wrapper?.__iftar_rc314) window.wafdIftarStageLoad(wrapper);
  });
  frappe.realtime.on("wafd_iftar_delivery_ready", () => {
    const wrapper = window.__wafdIftarTeamWrapper;
    if (wrapper?.__iftar_rc314) window.wafdIftarStageLoad(wrapper);
  });
})();
