frappe.pages['wafd-iftar-site'].on_page_load=function(wrapper){
  const page=frappe.ui.make_app_page({parent:wrapper,title:__('إدارة موقع إفطار الصائم'),single_column:true});
  $(wrapper).addClass('wafd-iftar-site-page');
  wrapper.__ifs={$root:$('<div class="ifs-wrap"></div>').appendTo(page.body),loading:false};
};
(function(){
 const esc=v=>frappe.utils.escape_html(String(v??''));
 const n=v=>Number(v||0).toLocaleString('en-US');
 const api=(m,args={})=>frappe.call({method:'wafd_one.wafd_one.iftar_stage_portal.'+m,args,freeze:false}).then(r=>r.message);
 const team=(m,args={})=>frappe.call({method:'wafd_one.wafd_one.iftar_team.'+m,args,freeze:false}).then(r=>r.message);
 function header(d){return `<div class="ifs-head"><small>WAFD ONE · IFTAR SAIM</small><h1>إدارة موقع إفطار الصائم</h1><p>الاستلام · الفحص · تسليم المشرفين · اعتماد التقارير</p><p style="margin-top:10px"><b>${esc(d.full_name||d.user)}</b></p></div>`}
 function steps(o){return `<div class="ifs-steps">
   <div class="ifs-step ${o?.site_receipt_approved?'done':''}"><b>${o?.site_receipt_approved?'✓ ':''}استلام الموقع</b><span>${o?.site_receipt_approved?n(o.site_received_meals)+' وجبة':'بانتظار وصول السائق'}</span></div>
   <div class="ifs-step ${o?.authority_inspection_approved?'done':''}"><b>${o?.authority_inspection_approved?'✓ ':''}فحص الجهة</b><span>${o?.authority_inspection_approved?'تم الفحص':'بعد الاستلام'}</span></div>
   <div class="ifs-step ${(o?.site_report_approved)?'done':''}"><b>${o?.site_report_approved?'✓ ':''}تقارير المشرفين</b><span>${o?.site_report_approved?'تم اعتماد التقرير':'متابعة وتقفيل اليوم'}</span></div>
 </div>`}
 function reports(p){
   const rows=p.supervisor_reports||[];
   if(!rows.length) return `<div class="ifs-empty">لم يتم إنشاء مهام المشرفين لهذا اليوم بعد.</div>`;
   return rows.map(r=>`<div class="ifs-report" data-report="${esc(r.name)}"><div class="ifs-report-head"><div><b>${esc(r.supervisor_name||r.supervisor_user||r.name)}</b><div class="ifs-muted">${n(r.planned_meals)} وجبة مسندة</div></div><div>${r.manager_approved?'✅ معتمد':r.report_submitted?'بانتظار اعتمادك':r.received_meals?'قيد التنفيذ':'بانتظار التسليم'}</div></div><div class="ifs-report-actions">
     ${!r.received_meals?`<button class="ifs-handover">تسليم الوجبات والعهدة</button>`:''}
     ${r.report_submitted&&!r.manager_approved?`<button class="ifs-approve-report">اعتماد تقرير المشرف</button>`:''}
   </div></div>`).join('')
 }
 function card(p){const o=p.site_operation;if(!o)return `<div class="ifs-card"><h3>${esc(p.project_title||p.name)}</h3><div class="ifs-empty">لا يوجد يوم تشغيل جاهز للموقع الآن.</div></div>`;
   const arrived=Math.max(Number(o.delivery_verified_meals||0),Number(o.delivered_meals||0));
   return `<div class="ifs-card" data-operation="${esc(o.name)}" data-project="${esc(p.name)}"><div class="ifs-muted">${esc(p.name)} · ${esc(o.operation_date||'')}</div><h3>${esc(p.project_title||p.distribution_site||p.name)}</h3><div class="ifs-muted">${esc(p.contracting_entity||'')} · ${esc(p.distribution_site||'')}</div><div class="ifs-grid"><div class="ifs-stat"><b>${n(o.planned_meals)}</b><span>المخطط</span></div><div class="ifs-stat"><b>${n(arrived)}</b><span>وصل ومثبت</span></div><div class="ifs-stat"><b>${n(o.site_received_meals)}</b><span>استلام الموقع</span></div><div class="ifs-stat"><b>${n((p.supervisor_reports||[]).length)}</b><span>المشرفون</span></div></div>${steps(o)}
   ${!o.site_receipt_approved&&arrived>0?`<button class="ifs-btn ifs-receive" data-max="${arrived}">اعتماد استلام الموقع</button>`:''}
   ${o.site_receipt_approved&&!o.authority_inspection_approved?`<button class="ifs-btn ifs-inspect">فحص الجهة واعتماد الجاهزية</button>`:''}
   ${o.authority_inspection_approved&&!(p.supervisor_reports||[]).length?`<button class="ifs-btn secondary ifs-create-reports">إنشاء مهام المشرفين لهذا اليوم</button>`:''}
   ${reports(p)}
   ${(p.supervisor_reports||[]).length&&p.supervisor_reports.every(r=>r.manager_approved)&&!o.site_report_approved?`<button class="ifs-btn ifs-finalize">اعتماد التقرير المجمع وإرسال المرحلة للإدارة</button>`:''}
   </div>`}
 function render(w,d){w.__ifs.data=d;w.__ifs.$root.html(header(d)+`<div class="ifs-title"><h2>مهام الموقع</h2><span>${(d.projects||[]).length}</span></div>`+((d.projects||[]).map(card).join('')||'<div class="ifs-empty">لا توجد مشاريع مسندة لهذا الحساب.</div>'));bind(w)}
 function bind(w){const $r=w.__ifs.$root;$r.off('.ifs');
   $r.on('click.ifs','.ifs-receive',function(){const op=$(this).closest('[data-operation]').data('operation'),max=Number($(this).data('max'));const d=new frappe.ui.Dialog({title:'اعتماد استلام الموقع',fields:[{fieldname:'received_meals',fieldtype:'Int',label:'عدد الوجبات المستلمة',default:max,reqd:1}],primary_action_label:'اعتماد الاستلام',primary_action:async v=>{await team('approve_site_receipt',{operation_name:op,received_meals:v.received_meals});d.hide();frappe.show_alert({message:'تم اعتماد استلام الموقع',indicator:'green'});loadSite(w)}});d.show()});
   $r.on('click.ifs','.ifs-inspect',function(){const op=$(this).closest('[data-operation]').data('operation');const d=new frappe.ui.Dialog({title:'فحص الجهة',fields:[{fieldname:'supervisor_name',fieldtype:'Data',label:'اسم مشرف التغذية',reqd:1},{fieldname:'photo',fieldtype:'Attach Image',label:'صورة الفحص',reqd:1},{fieldname:'yogurt_checked',fieldtype:'Check',label:'تم فحص الزبادي'},{fieldname:'bread_checked',fieldtype:'Check',label:'تم فحص الخبز'},{fieldname:'dates_checked',fieldtype:'Check',label:'تم فحص التمر'},{fieldname:'expiry_checked',fieldtype:'Check',label:'تم فحص تواريخ الصلاحية'},{fieldname:'notes',fieldtype:'Small Text',label:'ملاحظات'}],primary_action_label:'اعتماد الفحص',primary_action:async v=>{await team('approve_authority_inspection',{operation_name:op,...v});d.hide();frappe.show_alert({message:'تم اعتماد الفحص',indicator:'green'});loadSite(w)}});d.show()});
   $r.on('click.ifs','.ifs-create-reports',async function(){const op=$(this).closest('[data-operation]').data('operation');await team('ensure_supervisor_reports',{operation_name:op});frappe.show_alert({message:'تم إنشاء مهام المشرفين',indicator:'green'});loadSite(w)});
   $r.on('click.ifs','.ifs-handover',function(){const $x=$(this).closest('[data-report]'),report=$x.data('report');const p=w.__ifs.data.projects.find(p=>(p.supervisor_reports||[]).some(r=>r.name===report));const rr=(p.supervisor_reports||[]).find(r=>r.name===report);const d=new frappe.ui.Dialog({title:'تسليم المشرف',fields:[{fieldname:'received_meals',fieldtype:'Int',label:'عدد الوجبات',default:rr.planned_meals,reqd:1},{fieldname:'tablecloths',fieldtype:'Int',label:'عدد السفر'},{fieldname:'bread_bags',fieldtype:'Int',label:'أكياس الخبز'},{fieldname:'waste_bags',fieldtype:'Int',label:'أكياس النفايات'},{fieldname:'gloves',fieldtype:'Int',label:'القفازات'},{fieldname:'shoe_covers',fieldtype:'Int',label:'غطاء الأرجل'},{fieldname:'handover_photo',fieldtype:'Attach Image',label:'صورة تسليم العهدة',reqd:1}],primary_action_label:'تأكيد التسليم',primary_action:async v=>{await team('receive_for_supervisor',{report_name:report,...v});d.hide();frappe.show_alert({message:'تم تسليم المشرف',indicator:'green'});loadSite(w)}});d.show()});
   $r.on('click.ifs','.ifs-approve-report',function(){const report=$(this).closest('[data-report]').data('report');const d=new frappe.ui.Dialog({title:'اعتماد تقرير المشرف',fields:[{fieldname:'notes',fieldtype:'Small Text',label:'ملاحظات المدير'}],primary_action_label:'اعتماد التقرير',primary_action:async v=>{await team('approve_supervisor_report',{report_name:report,notes:v.notes||''});d.hide();frappe.show_alert({message:'تم اعتماد التقرير',indicator:'green'});loadSite(w)}});d.show()});
   $r.on('click.ifs','.ifs-finalize',async function(){const op=$(this).closest('[data-operation]').data('operation');await team('finalize_daily_report',{operation_name:op});frappe.show_alert({message:'تم اعتماد تقرير الموقع وإرساله للإدارة',indicator:'green'});loadSite(w)});
 }
 async function loadSite(w){if(!w?.__ifs||w.__ifs.loading)return;w.__ifs.loading=true;w.__ifs.$root.html('<div class="ifs-empty">جاري تحميل مهام الموقع…</div>');try{render(w,await api('get_site_portal_data'))}catch(e){console.error('WAFD Iftar Site load failed',e);w.__ifs.$root.html(`<div class="ifs-empty"><b>تعذر تحميل مهام الموقع</b><br>${esc(e.message||e)}<br><button class="ifs-btn ifs-retry" style="margin-top:14px">إعادة المحاولة</button></div>`);w.__ifs.$root.off('click.ifsretry').on('click.ifsretry','.ifs-retry',()=>loadSite(w))}finally{w.__ifs.loading=false}}
 frappe.pages['wafd-iftar-site'].on_page_show=function(wrapper){loadSite(wrapper)};
})();
