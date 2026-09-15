frappe.pages["wafd-iftar-team"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({parent:wrapper,title:__("فريق إفطار الصائم"),single_column:true});
  const $root=$(wrapper).find('.layout-main-section').html(`<div class="ift-wrap"><section class="ift-hero"><h2>تشغيل مشروع إفطار الصائم</h2><p class="ift-subtitle">واجهة الموظف حسب المهمة المسندة له</p><div class="ift-controls"><input type="date" class="form-control ift-date"><select class="form-control ift-project"><option value="">جميع المشاريع</option></select><button class="btn btn-light ift-refresh">تحديث</button></div></section><div class="ift-body"></div></div>`);
  $root.find('.ift-date').val(frappe.datetime.get_today());
  let data={projects:[],operations:[],reports:[],mode:''};
  const esc=v=>frappe.utils.escape_html(String(v||''));
  const num=v=>frappe.format(Number(v||0),{fieldtype:'Int'});
  const route=(dt,name)=>frappe.set_route('Form',dt,name);

  function shortcuts(){
    if(data.mode==='management') return `<div class="ift-shortcuts"><button class="ift-shortcut" data-page="wafd-iftar-wizard"><b>إنشاء مشروع</b><span>المدة والأعداد والأسعار والرواتب والتكاليف</span></button><button class="ift-shortcut" data-list="WAFD Iftar Supervisor Plan"><b>الفريق الشهري</b><span>المشرفون وأصحاب السفر والمساعدون</span></button><button class="ift-shortcut" data-list="WAFD Iftar Supervisor Daily Report"><b>تقارير المشرفين</b><span>المراجعة والاعتماد والتقرير المجمع</span></button><button class="ift-shortcut" data-page="wafd-iftar-operations"><b>لوحة الإدارة</b><span>جميع مؤشرات التشغيل اليومية</span></button></div>`;
    if(data.mode==='delivery') return `<div class="ift-shortcuts"><button class="ift-shortcut" data-page="wafd-delivery-supervisor"><b>جدول التوصيل الحالي</b><span>السائق والمركبة والموقع والكمية والتوقيت</span></button></div><div class="alert alert-info">لا ينشئ إفطار الصائم رحلة مكررة. تظهر للسائقين نفس عمليات جدول التوصيل الحالي، وتعود الكميات والصور وأوقات الوصول إلى هذه الشاشة.</div>`;
    return '';
  }
  function operations(){
    if(!data.operations.length) return `<div class="ift-empty">لا يوجد تشغيل معتمد في هذا التاريخ.</div>`;
    return `<div class="ift-grid">${data.operations.map(o=>{
      const pct=Number(o.completion_percent||0);
      const shortage=o.kitchen_shortage_reported?`<div class="ift-warning"><b>نقص مواد</b><br>${esc(o.kitchen_shortage_notes)}</div>`:'';
      const deliveries=(o.deliveries||[]).map(t=>`<div class="ift-delivery"><b>${esc(t.driver||'لم يحدد السائق')}</b> · ${esc(t.vehicle||'لم تحدد المركبة')}<br><span class="ift-muted">${esc(t.destination_name)} — ${num(t.quantity)} وجبة ${t.proof?'✓ موثق':''}</span></div>`).join('');
      let actions=`<button class="btn btn-default" data-open-op="${esc(o.name)}">فتح التفاصيل</button>`;
      if(data.mode==='management') actions+=`<button class="btn btn-default" data-assign="${esc(o.project)}">إسناد فريق المشروع</button><button class="btn btn-success" data-finalize="${esc(o.name)}">اعتماد التقرير الرسمي</button>`;
      if(data.mode==='kitchen') actions=`<button class="btn btn-primary" data-kitchen="${esc(o.name)}" data-ready="${o.kitchen_ready_meals||0}">تحديث المطبخ</button>`;
      if(data.mode==='site') actions=`<button class="btn btn-primary" data-generate="${esc(o.name)}">تجهيز تكليفات المشرفين</button>${!o.site_receipt_approved&&Number(o.delivery_verified_meals)>0?`<button class="btn btn-primary" data-site-receipt="${esc(o.name)}" data-arrived="${Number(o.delivery_verified_meals)||0}">اعتماد استلام الموقع</button>`:''}<button class="btn btn-default" data-open-op="${esc(o.name)}">فحص الجهة والتفاصيل</button><button class="btn btn-success" data-finalize="${esc(o.name)}">اعتماد التقرير الرسمي</button>`;
      if(data.mode==='delivery') actions=`<button class="btn btn-primary" data-page="wafd-delivery-supervisor">فتح جدول التوصيل</button>`;
      return `<article class="ift-card"><span class="ift-badge">${esc(o.status)}</span><h4>${esc(o.project_title)}</h4><div class="ift-row"><span>المخطط</span><b>${num(o.planned_meals)} وجبة · ${num(o.cartons)} كرتون</b></div><div class="ift-row"><span>جاهز من المطبخ</span><b>${num(o.kitchen_ready_meals)}</b></div><div class="ift-row"><span>وصول السائق المثبت</span><b>${num(o.delivery_verified_meals)} · ${num(o.delivery_proof_count)} إثبات</b></div><div class="ift-row"><span>اعتماد مدير الموقع</span><b>${num(o.site_received_meals)} ${o.site_receipt_approved?'✓':''}</b></div><div class="ift-row"><span>المسلّم للمشرفين</span><b>${num(o.received_meals)}</b></div><div class="ift-progress"><i style="width:${Math.min(100,pct)}%"></i></div>${shortage}${deliveries}${actions}</article>`;
    }).join('')}</div>`;
  }
  function reports(){
    if(!['management','site','supervisor'].includes(data.mode)) return '';
    const list=data.reports||[];
    return `<h3 class="ift-title">تقارير المشرفين</h3>${list.length?`<div class="ift-grid">${list.map(r=>`<article class="ift-card"><span class="ift-badge">${r.manager_approved?'معتمد':r.report_submitted?'بانتظار الاعتماد':'قيد العمل'}</span><h4>${esc(r.supervisor_name)}</h4><div class="ift-row"><span>المسند</span><b>${num(r.planned_meals)} · ${num(r.cartons)} كرتون</b></div><div class="ift-row"><span>المستلم / الموزع</span><b>${num(r.received_meals)} / ${num(r.distributed_meals)}</b></div><button class="btn btn-default" data-report="${esc(r.name)}">فتح التقرير</button>${data.mode==='site'&&!r.received_meals?`<button class="btn btn-primary" data-receive="${esc(r.name)}" data-planned="${r.planned_meals||0}">تسليم العهدة</button>`:''}${data.mode==='site'&&r.report_submitted&&!r.manager_approved?`<button class="btn btn-success" data-approve="${esc(r.name)}">اعتماد التقرير</button>`:''}</article>`).join('')}</div>`:`<div class="ift-empty">لم تنشأ تقارير المشرفين لهذا اليوم بعد.</div>`}`;
  }
  function render(){
    const labels={management:'شاشة الإدارة ومدير المشروع',kitchen:'شاشة مشرف المطبخ',delivery:'شاشة مشرف التوصيل',site:'شاشة مدير الموقع',supervisor:'شاشة المشرف الميداني'};
    $root.find('.ift-subtitle').text(labels[data.mode]||'واجهة الموظف حسب المهمة');
    const total=data.operations.reduce((s,x)=>s+Number(x.planned_meals||0),0);
    const ready=data.operations.reduce((s,x)=>s+Number(x.kitchen_ready_meals||0),0);
    $root.find('.ift-body').html(`${shortcuts()}<div class="ift-kpis"><div class="ift-kpi"><span>المشاريع اليوم</span><strong>${data.operations.length}</strong></div><div class="ift-kpi"><span>الوجبات</span><strong>${num(total)}</strong></div><div class="ift-kpi"><span>الجاهز</span><strong>${num(ready)}</strong></div><div class="ift-kpi"><span>تقارير المشرفين</span><strong>${(data.reports||[]).length}</strong></div></div><h3 class="ift-title">تشغيل اليوم</h3>${operations()}${reports()}`);
  }
  async function load(){
    const res=await frappe.call({method:'wafd_one.wafd_one.iftar_team.get_team_dashboard',args:{date:$root.find('.ift-date').val(),project:$root.find('.ift-project').val()||null},freeze:true});
    data=res.message||{};
    const current=$root.find('.ift-project').val();
    $root.find('.ift-project').html(`<option value="">جميع المشاريع</option>${(data.projects||[]).map(p=>`<option value="${esc(p.name)}">${esc(p.project_title)} — ${esc(p.distribution_site)}</option>`).join('')}`).val(current||'');
    render();
  }
  $root.on('click','[data-page]',function(){frappe.set_route($(this).data('page'));});
  $root.on('click','[data-list]',function(){frappe.set_route('List',$(this).data('list'));});
  $root.on('click','[data-open-op]',function(){route('WAFD Iftar Daily Operation',$(this).data('open-op'));});
  $root.on('click','[data-report]',function(){route('WAFD Iftar Supervisor Daily Report',$(this).data('report'));});
  $root.on('click','[data-kitchen]',function(){const name=$(this).data('kitchen');const d=new frappe.ui.Dialog({title:'جاهزية المطبخ والنواقص',fields:[{fieldname:'ready_meals',fieldtype:'Int',label:'العدد الجاهز',reqd:1,default:$(this).data('ready')},{fieldname:'shortage_reported',fieldtype:'Check',label:'يوجد نقص مواد'},{fieldname:'shortage_notes',fieldtype:'Small Text',label:'بيان المواد الناقصة',depends_on:'shortage_reported'},{fieldname:'approve',fieldtype:'Check',label:'اعتماد الجاهزية'}],primary_action_label:'حفظ وإرسال',primary_action:async v=>{await frappe.call({method:'wafd_one.wafd_one.iftar_team.update_kitchen',args:{operation_name:name,...v},freeze:true});d.hide();load();}});d.show();});
  $root.on('click','[data-generate]',async function(){const res=await frappe.call({method:'wafd_one.wafd_one.iftar_team.ensure_supervisor_reports',args:{operation_name:$(this).data('generate')},freeze:true});const x=res.message||{};if(!Number(x.total_plans||0))frappe.msgprint({title:'لم يسجل فريق المشرفين',message:'يجب أن تسجل الإدارة خطة لكل مشرف وتربطها بحسابه وأصحاب السفر والمساعدين أولاً.',indicator:'orange'});else if((x.skipped_without_user||[]).length)frappe.msgprint(`لم تُنشأ تقارير لمن لم يربط حسابهم بالخطة: ${x.skipped_without_user.join('، ')}`);load();});
  $root.on('click','[data-assign]',function(){
    const projectName=$(this).data('assign');
    const project=(data.projects||[]).find(p=>p.name===projectName)||{};
    const d=new frappe.ui.Dialog({title:'إسناد فريق المشروع الثابت',fields:[
      {fieldname:'project_manager_user',fieldtype:'Link',options:'User',label:'مدير المشروع',default:project.project_manager_user||'',get_query:()=>({filters:{enabled:1,user_type:'System User'}})},
      {fieldname:'kitchen_supervisor_user',fieldtype:'Link',options:'User',label:'مشرف المطبخ',default:project.kitchen_supervisor_user||'',get_query:()=>({filters:{enabled:1,user_type:'System User'}})},
      {fieldname:'delivery_supervisor_user',fieldtype:'Link',options:'User',label:'مشرف التوصيل',default:project.delivery_supervisor_user||'',get_query:()=>({filters:{enabled:1,user_type:'System User'}})},
      {fieldname:'site_manager_user',fieldtype:'Link',options:'User',label:'مدير الموقع',default:project.site_manager_user||'',get_query:()=>({filters:{enabled:1,user_type:'System User'}})},
      {fieldtype:'HTML',fieldname:'help',options:'<div class="alert alert-info">يسجل هذا الفريق مرة واحدة ويستخدم طوال المشروع. بعد الحفظ تظهر عمليات المشروع تلقائياً لكل موظف حسب حسابه.</div>'}
    ],primary_action_label:'حفظ الإسناد',primary_action:async v=>{await frappe.call({method:'wafd_one.wafd_one.iftar_team.assign_project_team',args:{project_name:projectName,...v},freeze:true});d.hide();frappe.show_alert({message:'تم إسناد فريق المشروع',indicator:'green'},4);load();}});d.show();
  });
  $root.on('click','[data-site-receipt]',function(){const name=$(this).data('site-receipt');const d=new frappe.ui.Dialog({title:'اعتماد استلام مدير الموقع',fields:[{fieldname:'received_meals',fieldtype:'Int',label:'العدد المستلم',reqd:1,default:$(this).data('arrived')}],primary_action_label:'اعتماد الاستلام',primary_action:async v=>{await frappe.call({method:'wafd_one.wafd_one.iftar_team.approve_site_receipt',args:{operation_name:name,received_meals:v.received_meals},freeze:true});d.hide();load();}});d.show();});
  $root.on('click','[data-receive]',function(){const name=$(this).data('receive');const d=new frappe.ui.Dialog({title:'تسليم الوجبات والعهدة للمشرف',fields:[{fieldname:'received_meals',fieldtype:'Int',label:'عدد الوجبات',reqd:1,default:$(this).data('planned')},{fieldname:'tablecloths',fieldtype:'Int',label:'السفر'},{fieldname:'bread_bags',fieldtype:'Int',label:'أكياس الخبز'},{fieldname:'waste_bags',fieldtype:'Int',label:'أكياس النفايات'},{fieldname:'gloves',fieldtype:'Int',label:'القفازات'},{fieldname:'shoe_covers',fieldtype:'Int',label:'غطاء الأرجل'}],primary_action_label:'اعتماد التسليم',primary_action:async v=>{await frappe.call({method:'wafd_one.wafd_one.iftar_team.receive_for_supervisor',args:{report_name:name,...v},freeze:true});d.hide();load();}});d.show();});
  $root.on('click','[data-approve]',async function(){await frappe.call({method:'wafd_one.wafd_one.iftar_team.approve_supervisor_report',args:{report_name:$(this).data('approve')},freeze:true});load();});
  $root.on('click','[data-finalize]',async function(){const name=$(this).data('finalize');await frappe.call({method:'wafd_one.wafd_one.iftar_team.finalize_daily_report',args:{operation_name:name},freeze:true});frappe.show_alert({message:'تم اعتماد وتجميع التقرير الرسمي',indicator:'green'},5);load();});
  $root.find('.ift-refresh').on('click',load);$root.find('.ift-date,.ift-project').on('change',load);load();
};
