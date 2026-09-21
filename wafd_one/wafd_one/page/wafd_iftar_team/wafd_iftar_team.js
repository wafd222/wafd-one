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
      project_manager: "مدير المشروع · إعداد فريق الموقع وتوزيع الوجبات",
      kitchen: "مشرف المطبخ · الإنتاج والتغليف والتحميل وتوزيع السيارات",
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
    const allocated = Boolean(Number(o.delivery_plan_approved || 0));
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
      ${load && !allocated ? '<button type="button" class="btn btn-dark ift-primary ift-open-allocation">توزيع الوجبات المحملة على السيارات</button>' : ''}
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
      ${!externalView ? `<div class="ift-team-summary"><span><b>مدير المشروع</b>${esc(p.project_manager_user || 'غير مسند')}</span><span><b>مشرف المطبخ</b>${esc(p.kitchen_supervisor_user || 'غير مسند')}</span><span><b>مشرف التوصيل</b>${esc(p.delivery_supervisor_user || 'غير مسند')}</span><span><b>مدير الموقع</b>${esc(p.site_manager_user || 'غير مسند')}</span><span><b>مشرفو السفر</b>${esc((p.supervisor_plans || []).filter(x => Number(x.active) !== 0).map(x => x.supervisor_name || x.supervisor_user).filter(Boolean).join('، ') || 'غير مسند')}</span><span><b>المتابع الخارجي</b>${esc(p.external_viewer_user || 'غير مسند')}</span></div>` : '<div class="ift-success">متابعة للقراءة فقط — لا يمكن تعديل أو اعتماد أي مرحلة.</div>'}
      ${canAssign ? '<div class="ift-actions"><button class="btn btn-default ift-open-employees">إدارة الموظفين والمهمات</button><button class="btn btn-default ift-open-legacy">فتح إدارة إفطار الصائم</button></div>' : ''}
    </div>`;
  }

  function projectManagerCard(p) {
    const plans = (p.supervisor_plans || []).filter(x => Number(x.active) !== 0);
    const assistants = plans.reduce((sum, x) => sum + (x.assistants || []).filter(a => Number(a.active) !== 0).length, 0);
    const owners = plans.reduce((sum, x) => sum + (x.table_owners || []).length, 0);
    const allocated = plans.reduce((sum, x) => sum + (x.table_owners || []).reduce((s, o) => s + Number(o.meal_quantity || 0), 0), 0);
    return `<div class="ift-project-card admin-project" data-project="${esc(p.name)}">
      ${projectIdentity(p)}
      <div class="ift-manager-project-summary"><b>${num(p.daily_meals)} وجبة</b><span>${esc(p.distribution_site || '—')}</span><span>${fmtDate(p.start_date)}${p.end_date && p.end_date !== p.start_date ? ` — ${fmtDate(p.end_date)}` : ''}</span></div>
      <div class="ift-entry-grid">
        <button type="button" class="ift-entry-card ift-setup-staff"><span>المشرفون والمساعدون</span><b>${num(plans.length)} مشرف · ${num(assistants)} مساعد</b><small>تسجيل الأسماء وأرقام الجوالات</small></button>
        <button type="button" class="ift-entry-card ift-setup-owners"><span>أصحاب السفر وتوزيع الوجبات</span><b>${num(owners)} صاحب سفرة · ${num(allocated)} وجبة</b><small>الوجبات والكراتين والخبز والسفر</small></button>
      </div>
      ${p.current_operation ? `<div class="ift-monitor-day"><span>اليوم ${num(p.current_operation.day_index)} من ${num(p.current_operation.day_total)}</span><b>${fmtDate(p.current_operation.operation_date)}</b></div>` : ''}
    </div>`;
  }

  function pmUserOptions(users, selected) {
    return '<option value="">اختر حساب المشرف</option>' + (users || []).map(u => `<option value="${esc(u.value)}" ${u.value === selected ? 'selected' : ''}>${esc(u.label)} · ${esc(u.value)}</option>`).join('');
  }

  function pmOwnerRow(owner = {}, capacity = 25) {
    const cartons = Math.ceil(Number(owner.meal_quantity || 0) / Math.max(Number(capacity || 25), 1));
    return `<div class="ift-pm-owner">
      <div class="ift-pm-row"><input class="form-control po-name" placeholder="اسم صاحب السفرة" value="${esc(owner.table_owner_name || '')}"><input class="form-control po-mobile" placeholder="رقم الجوال" value="${esc(owner.mobile_no || '')}"></div>
      <div class="ift-pm-row four"><input class="form-control po-meals" type="number" min="1" placeholder="الوجبات" value="${esc(owner.meal_quantity || '')}"><input class="form-control po-bread" type="number" min="0" placeholder="الخبز" value="${esc(owner.bread_quantity || 0)}"><input class="form-control po-tables" type="number" min="0" placeholder="السفر" value="${esc(owner.tablecloths_quantity || 0)}"><span class="ift-cartons" data-capacity="${esc(capacity)}">${num(cartons)} كرتون</span></div>
      <input class="form-control po-point" placeholder="الموقع" value="${esc(owner.distribution_point || '')}"><button type="button" class="btn btn-xs btn-default po-remove">حذف صاحب السفرة</button>
    </div>`;
  }

  function pmAssistantRow(a = {}) {
    return `<div class="ift-pm-row assistant"><input class="form-control pa-name" placeholder="اسم المساعد" value="${esc(a.assistant_name || '')}"><input class="form-control pa-mobile" placeholder="رقم الجوال" value="${esc(a.mobile_no || '')}"><button type="button" class="btn btn-default pa-remove">حذف</button></div>`;
  }

  function pmSupervisorCard(users, plan = {}, capacity = 25) {
    const owners = (plan.table_owners?.length ? plan.table_owners : [{}]).map(x => pmOwnerRow(x, capacity)).join('');
    const assistants = (plan.assistants || []).map(pmAssistantRow).join('');
    return `<section class="ift-pm-supervisor" data-plan="${esc(plan.name || '')}"><div class="ift-pm-title"><b>المشرف وفريقه</b><button type="button" class="btn btn-xs btn-default ps-remove">حذف المشرف</button></div><select class="form-control ps-user">${pmUserOptions(users, plan.supervisor_user || '')}</select><div class="ift-pm-row"><input class="form-control ps-name" placeholder="اسم المشرف" value="${esc(plan.supervisor_name || '')}"><input class="form-control ps-mobile" placeholder="رقم جوال المشرف" value="${esc(plan.supervisor_mobile || '')}"></div><h5>المساعدون التابعون للمشرف</h5><div class="ps-assistants">${assistants}</div><button type="button" class="btn btn-sm btn-default ps-add-assistant">+ إضافة مساعد</button><h5>أصحاب السفر المسندون للمشرف وفريقه</h5><div class="ps-owners">${owners}</div><button type="button" class="btn btn-sm btn-default ps-add-owner">+ إضافة صاحب سفرة</button></section>`;
  }

  function openProjectSetupDialog(wrapper, projectName) {
    const data = wrapper.__iftar_rc314.data;
    const p = (data.projects || []).find(x => x.name === projectName);
    if (!p) return;
    const users = data.supervisor_options || [];
    const capacity = Number(p.max_carton_capacity || 25);
    const d = new frappe.ui.Dialog({title:"إعداد المشرفين والمساعدين وأصحاب السفر",size:"extra-large",fields:[{fieldname:"summary",fieldtype:"HTML"},{fieldname:"setup",fieldtype:"HTML"}],primary_action_label:"حفظ الفريق والتوزيع",primary_action:async()=>{
      const plans=[];
      d.$wrapper.find('.ift-pm-supervisor').each(function(){const $s=$(this),table_owners=[],assistants=[];$s.find('.ift-pm-owner').each(function(){const $o=$(this),name=$o.find('.po-name').val().trim(),meal=Number($o.find('.po-meals').val()||0);if(name||meal)table_owners.push({table_owner_name:name,mobile_no:$o.find('.po-mobile').val().trim(),meal_quantity:meal,bread_quantity:Number($o.find('.po-bread').val()||0),tablecloths_quantity:Number($o.find('.po-tables').val()||0),distribution_point:$o.find('.po-point').val().trim()})});$s.find('.assistant').each(function(){const $a=$(this),name=$a.find('.pa-name').val().trim();if(name)assistants.push({assistant_name:name,mobile_no:$a.find('.pa-mobile').val().trim(),active:1})});plans.push({name:$s.data('plan')||'',supervisor_user:$s.find('.ps-user').val(),supervisor_name:$s.find('.ps-name').val().trim(),supervisor_mobile:$s.find('.ps-mobile').val().trim(),table_owners,assistants})});
      if(!plans.length)return frappe.msgprint('أضف مشرفاً واحداً على الأقل');
      const total=plans.reduce((a,x)=>a+x.table_owners.reduce((b,o)=>b+Number(o.meal_quantity||0),0),0);
      if(total!==Number(p.daily_meals||0))return frappe.msgprint(`إجمالي الوجبات الموزعة ${num(total)} ويجب أن يساوي ${num(p.daily_meals)} وجبة.`);
      d.get_primary_btn().prop('disabled',true);try{await call('save_quick_supervisor_setup',{project_name:projectName,plans_json:JSON.stringify(plans)});d.hide();frappe.show_alert({message:'تم حفظ الفريق والتوزيع وظهرت البيانات للمشرفين',indicator:'green'});await window.wafdIftarStageLoad(wrapper)}catch(e){d.get_primary_btn().prop('disabled',false);throw e}
    }});
    d.show();
    d.fields_dict.summary.$wrapper.html(`<div class="ift-pm-dialog-summary"><b>${esc(p.project_title || p.name)}</b><span>${num(p.daily_meals)} وجبة · ${num(p.cartons_per_day)} كرتون · ${esc(p.distribution_site || '')}</span></div>`);
    const $box=$('<div class="ift-pm-setup"></div>');d.fields_dict.setup.$wrapper.empty().append($box);
    const plans=(p.supervisor_plans?.length?p.supervisor_plans.filter(x=>Number(x.active)!==0):[{table_owners:[{meal_quantity:p.daily_meals||0,distribution_point:p.distribution_site||''}]}]);plans.forEach(x=>$box.append(pmSupervisorCard(users,x,capacity)));$box.append('<button type="button" class="btn btn-default ps-add-supervisor">+ إضافة مشرف آخر</button>');
    d.$wrapper.on('change','.ps-user',function(){const u=users.find(x=>x.value===$(this).val()),$s=$(this).closest('.ift-pm-supervisor');if(u){if(!$s.find('.ps-name').val())$s.find('.ps-name').val(u.label);if(!$s.find('.ps-mobile').val())$s.find('.ps-mobile').val(u.mobile_no||'')}}).on('click','.ps-add-owner',function(){$(this).siblings('.ps-owners').append(pmOwnerRow({},capacity))}).on('click','.ps-add-assistant',function(){$(this).siblings('.ps-assistants').append(pmAssistantRow())}).on('click','.po-remove',function(){$(this).closest('.ift-pm-owner').remove()}).on('click','.pa-remove',function(){$(this).closest('.assistant').remove()}).on('click','.ps-remove',function(){if(d.$wrapper.find('.ift-pm-supervisor').length>1)$(this).closest('.ift-pm-supervisor').remove();else frappe.show_alert({message:'يجب وجود مشرف واحد على الأقل',indicator:'orange'})}).on('click','.ps-add-supervisor',function(){$(this).before(pmSupervisorCard(users,{},capacity))}).on('input','.po-meals',function(){const $c=$(this).closest('.ift-pm-owner').find('.ift-cartons'),qty=Number($(this).val()||0);$c.text(`${num(Math.ceil(qty/Math.max(capacity,1)))} كرتون`)});
  }

  function reportInbox(data) {
    const rows = data.report_inbox || [];
    if (!rows.length) return `<div class="ift-section-title"><h2>التقارير اليومية</h2><span>0</span></div>${emptyState("لا توجد تقارير معتمدة من مدير الموقع حتى الآن")}`;
    return `<div class="ift-section-title"><h2>التقارير اليومية للإدارة</h2><span>${rows.length}</span></div><div class="ift-report-inbox">${rows.map(r => `<div class="ift-report-inbox-card" data-operation="${esc(r.name)}">
      <div class="ift-card-top"><span class="ift-state ${r.administration_report_approved ? 'done' : 'working'}">${r.administration_report_approved ? 'معتمد من الإدارة' : 'بانتظار اعتماد الإدارة'}</span><small>${esc(fmtDate(r.operation_date))}</small></div>
      <h3>${esc(r.project_title || r.project)}</h3><p>${esc(r.distribution_site || '')} · ${esc(r.contracting_entity || '')}</p>
      <div class="ift-numbers four"><div><b>${num(r.planned_meals)}</b><span>المخطط</span></div><div><b>${num(r.received_meals)}</b><span>المستلم</span></div><div><b>${num(r.supervisor_count)}</b><span>المشرفون</span></div><div><b>${num(Number(r.surplus_meals||0)+Number(r.preservation_society_quantity||0)+Number(r.waste_meals||0))}</b><span>الفائض والمعالجة</span></div></div>
      <div class="ift-report-status">${r.administration_report_approved ? `✓ الاعتماد النهائي ${esc(fmtTime(r.administration_report_approved_at))}` : `✓ اعتمده مدير الموقع ${esc(fmtTime(r.site_report_approved_at))}`}</div>
      <div class="ift-actions"><button class="btn btn-default ift-open-official-report">معاينة التقرير الرسمي</button>${['management','project_manager'].includes(data.mode) && !r.administration_report_approved ? '<button class="btn btn-dark ift-admin-approve-report">اعتماد مدير المشروع وإرساله للرئاسة</button>' : ''}</div>
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
    const pdfReady=fetch(urls.pdf,{credentials:"same-origin"}).then(async response=>{const type=(response.headers.get("content-type")||"").toLowerCase();if(!response.ok||!type.includes("application/pdf"))throw new Error("تعذر إنشاء ملف PDF");const blob=await response.blob();if(!blob.size)throw new Error("ملف PDF فارغ");return blob}).then(blob=>{cachedPdf=blob;$share.prop("disabled",false).removeAttr("title");return blob}).catch(error=>{pdfFailure=error;$share.prop("disabled",true).attr("title","تعذر تجهيز ملف PDF");return null});
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
    } else if (data.mode === "project_manager") {
      content = `<div class="ift-section-title"><h2>المشاريع المعتمدة</h2><span>${(data.projects || []).length}</span></div><div class="ift-project-list">${(data.projects || []).map(projectManagerCard).join('')}</div>`;
      if (!(data.projects || []).length) content += emptyState("لا توجد مشاريع معتمدة ومسندة لهذا الحساب");
      content += reportInbox(data);
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

    $root.on("click.rc314", ".ift-setup-staff, .ift-setup-owners", function () {
      openProjectSetupDialog(wrapper, String($(this).closest("[data-project]").data("project")));
    });

    $root.on("click.rc314", ".ift-open-employees", function () { frappe.set_route("wafd-employee-team"); });
    $root.on("click.rc314", ".ift-open-legacy", function () { frappe.set_route("wafd-iftar-operations"); });
    $root.on("click.rc314", ".ift-open-official-report", function () {
      const operation = String($(this).closest("[data-operation]").data("operation"));
      openOfficialReportPreview(operation);
    });
    $root.on("click.rc314", ".ift-admin-approve-report", function () {
      const operation = String($(this).closest("[data-operation]").data("operation"));
      const d = new frappe.ui.Dialog({title:"اعتماد مدير المشروع والتقرير النهائي",fields:[
        {fieldname:"recipient",fieldtype:"Data",label:"الجهة المستلمة",default:"رئاسة شؤون الحرمين",reqd:1},
        {fieldname:"administration_signature",fieldtype:"Signature",label:"توقيع مدير المشروع",reqd:1},
        {fieldname:"administration_stamp",fieldtype:"Attach Image",label:"ختم الشركة",reqd:1},
        {fieldname:"administration_notes",fieldtype:"Small Text",label:"ملاحظات مدير المشروع"}
      ],primary_action_label:"اعتماد وإرسال للرئاسة",primary_action:async values=>{
        d.get_primary_btn().prop("disabled",true);
        try{
          await frappe.call({method:"wafd_one.wafd_one.iftar_team.send_authority_report",args:{operation_name:operation,...values},freeze:true,freeze_message:"جاري اعتماد التقرير النهائي..."});
          d.hide();frappe.show_alert({message:"تم اعتماد مدير المشروع وإرسال التقرير للرئاسة",indicator:"green"});await window.wafdIftarStageLoad(wrapper);
        }catch(e){d.get_primary_btn().prop("disabled",false);throw e;}
      }});d.show();
    });
  }

  function openAllocationDialog(wrapper, operationName) {
    const data = wrapper.__iftar_rc314.data;
    const p = (data.projects || []).find(x => (x.pending_tasks || []).some(o => o.name === operationName) || x.task?.name === operationName);
    const o = p && ((p.pending_tasks || []).find(x => x.name === operationName) || (p.task?.name === operationName ? p.task : null));
    if (!p || !o) return;
    const vehicles = data.vehicles || [], drivers = data.drivers || [];
    const vopts = vehicles.map(v => `<option value="${esc(v.name)}">${esc(v.plate_number || v.name)}${v.capacity_meals ? ` · سعة ${num(v.capacity_meals)}` : ''}</option>`).join('');
    const dopts = drivers.map(v => `<option value="${esc(v.name)}">${esc(v.driver_name || v.name)}</option>`).join('');
    const d = new frappe.ui.Dialog({ title:`توزيع ${num(o.loaded_meals)} وجبة · ${num(o.cartons)} كرتون`, size:"large", fields:[{fieldname:"html",fieldtype:"HTML"},{fieldname:"note",fieldtype:"Small Text",label:"ملاحظات عامة تنتقل حتى التسليم"}], primary_action_label:"اعتماد توزيع السيارات", primary_action: async values => {
      const rows = [];
      d.$wrapper.find(".ift-alloc-row").each(function(){ const $r=$(this); const q=Number($r.find(".qty").val()||0); if($r.find(".vehicle").val() || $r.find(".driver").val() || q){ rows.push({vehicle:$r.find(".vehicle").val(),driver:$r.find(".driver").val(),quantity:q,bread_quantity:Number($r.find(".bread").val()||0),carts:Number($r.find(".carts").val()||0),tablecloths:Number($r.find(".tablecloths").val()||0),waste_bags:Number($r.find(".waste-bags").val()||0),gloves:Number($r.find(".gloves").val()||0),masks:Number($r.find(".masks").val()||0),shoe_covers:Number($r.find(".shoe-covers").val()||0),note:$r.find(".row-note").val()||""}); }});
      d.get_primary_btn().prop("disabled", true);
      try { await call("approve_delivery_plan", {operation_name:operationName, allocations:rows, note:values.note || ""}); d.hide(); frappe.show_alert({message:"تم اعتماد خطة التوصيل وإرسال الرحلات للسائقين",indicator:"green"}); await window.wafdIftarStageLoad(wrapper); }
      catch(e){ d.get_primary_btn().prop("disabled", false); throw e; }
    }});
    d.show();
    const $h = d.fields_dict.html.$wrapper;
    $h.html(`<div class="ift-allocation"><div class="ift-allocation-summary"><b>${num(o.loaded_meals)} وجبة</b><span>${num(o.cartons)} كرتون · ${esc(p.distribution_site || '')}</span></div><div class="ift-alloc-rows"></div><button type="button" class="btn btn-default ift-add-vehicle">+ إضافة سيارة</button><div class="ift-allocation-total">الموزع: <b>0</b> / ${num(o.loaded_meals)} وجبة</div></div>`);
    const add = () => {
      $h.find(".ift-alloc-rows").append(`<div class="ift-alloc-row"><select class="form-control vehicle"><option value="">اختر السيارة</option>${vopts}</select><select class="form-control driver"><option value="">اختر السائق</option>${dopts}</select><input class="form-control qty" type="number" min="1" placeholder="عدد الوجبات"><input class="form-control row-note" type="text" placeholder="ملاحظة السيارة (اختياري)"><button type="button" class="btn btn-default remove">×</button><div class="ift-alloc-supplies"><input class="form-control bread" type="number" min="0" placeholder="الخبز"><input class="form-control carts" type="number" min="0" placeholder="العربيات"><input class="form-control tablecloths" type="number" min="0" placeholder="السفر"><input class="form-control waste-bags" type="number" min="0" placeholder="أكياس النفايات"><input class="form-control gloves" type="number" min="0" placeholder="القفازات"><input class="form-control masks" type="number" min="0" placeholder="الكمامات"><input class="form-control shoe-covers" type="number" min="0" placeholder="غطاء الأرجل"></div></div>`);
    };
    const total = () => { let s=0; $h.find(".qty").each(function(){s += Number($(this).val()||0);}); $h.find(".ift-allocation-total b").text(num(s)); $h.find(".ift-allocation-total").toggleClass("ok", s === Number(o.loaded_meals||0)); };
    add(); $h.on("click", ".ift-add-vehicle", add); $h.on("click", ".remove", function(){ $(this).closest(".ift-alloc-row").remove(); total(); }); $h.on("input change", ".qty", total);
  }

  window.wafdIftarStageLoad = async function (wrapper) {
    const state = wrapper.__iftar_rc314;
    if (!state || state.loading) return;
    state.loading = true;
    state.$root.html('<div class="ift-loading">جاري تحميل مهام إفطار الصائم…</div>');
    try {
      const requested_mode = sessionStorage.getItem("wafd_iftar_requested_mode") || "";
      render(wrapper, await call("get_portal_data", {requested_mode}));
    }
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
