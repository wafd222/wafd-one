frappe.pages['wafd-iftar-report-center'].on_page_load=function(wrapper){
  frappe.ui.make_app_page({parent:wrapper,title:__('مركز تقارير إفطار الصائم'),single_column:true});
  wrapper.wafd_report_build=()=>build_report_center(wrapper);
};

frappe.pages['wafd-iftar-report-center'].on_page_show=function(wrapper){
  if(wrapper.wafd_report_build)wrapper.wafd_report_build();
};

async function build_report_center(wrapper){
  const $section=$(wrapper).find('.layout-main-section').off('.wafdReportCenter').attr('dir','rtl').empty();
  const $r=$(`<div class="irc">
    <div class="irc-head"><div><span>WAFD IFTAR PRO</span><h2>مركز التقارير والطباعة</h2><p>اختر مشروعاً، ثم افتح جميع مستنداته وتقاريره من مكان واحد.</p></div><button type="button" class="btn irc-back">لوحة التشغيل اليومية</button></div>
    <div class="irc-toolbar"><div class="irc-select"></div><div class="irc-project-meta">اختر مشروعاً لعرض مستنداته</div></div>
    <div class="irc-section-title">المستندات الأساسية</div><div class="irc-grid irc-primary"></div>
    <div class="irc-section-title">المتابعة والتحليل</div><div class="irc-grid irc-secondary"></div>
  </div>`).appendTo($section);

  const pc=frappe.ui.form.make_control({parent:$r.find('.irc-select'),df:{fieldtype:'Link',fieldname:'project',options:'WAFD Iftar Project',label:'المشروع',reqd:1,placeholder:'اختر مشروع إفطار صائم'},render_input:true});
  const routeOptions=frappe.route_options||{}; frappe.route_options=null;

  const primary=[
    {icon:'📄',title:'ملخص المشروع',desc:'ملخص تنفيذي ومالي للمشروع',type:'project_print',format:'WAFD Iftar Project Summary'},
    {icon:'🥤',title:'مكونات الوجبة والتسعير',desc:'الأصناف والكميات ومصادر الأسعار',type:'project_print',format:'WAFD Iftar Ingredients Report'},
    {icon:'💰',title:'التكاليف والربحية',desc:'الكرتون والسفر والعمالة والنقل والربح',type:'project_print',format:'WAFD Iftar Costing Report'},
    {icon:'📦',title:'خطة التوزيع والكراتين',desc:'أصحاب السفر والكميات والكراتين',type:'project_print',format:'WAFD Iftar Distribution & Cartons'},
    {icon:'📊',title:'التقرير التشغيلي اليومي',desc:'الإنتاج والتغليف والتحميل والتسليم والاستلام',type:'operation_print',format:'WAFD Iftar Daily Stage Report'},
    {icon:'🤝',title:'التسليم والاستلام اليومي',desc:'النموذج الرسمي للتوقيع والاستلام',type:'operation_print',format:'إفطار صائم — تسليم واستلام يومي'},
    {icon:'👥',title:'كشف المشرف والمساعدين',desc:'الوجبات والحضور والغياب حتى 100 مساعد',type:'operation_print',format:'WAFD Iftar Supervisor Receipt'},
    {icon:'🗂️',title:'جميع سجلات التشغيل اليومية',desc:'فتح قائمة كل أيام المشروع',type:'list',doctype:'WAFD Iftar Daily Operation'}
  ];
  const secondary=[
    {icon:'🧾',title:'تعديل تكاليف التشغيل',desc:'إضافة أو تعديل أي اتفاق تشغيلي',type:'project_form',anchor:'advanced_tab'},
    {icon:'📦',title:'تعديل خطة التوزيع',desc:'أصحاب السفر والكراتين والمركبات',type:'project_form',anchor:'advanced_tab'},
    {icon:'👤',title:'إدارة المشرفين والمساعدين',desc:'من سجل التشغيل اليومي',type:'list',doctype:'WAFD Iftar Daily Operation'},
    {icon:'📊',title:'لوحة التشغيل اليومية',desc:'متابعة المشروع من الإنتاج حتى الاستلام',type:'page',page:'wafd-iftar-operations'}
  ];
  const cardHtml=(c,i,g)=>`<button type="button" class="irc-card" data-group="${g}" data-i="${i}"><span class="irc-icon">${c.icon}</span><span class="irc-copy"><b>${c.title}</b><small>${c.desc}</small></span><span class="irc-arrow">←</span></button>`;
  $r.find('.irc-primary').html(primary.map((c,i)=>cardHtml(c,i,'p')).join(''));
  $r.find('.irc-secondary').html(secondary.map((c,i)=>cardHtml(c,i,'s')).join(''));

  async function updateMeta(project){
    if(!project){$r.find('.irc-project-meta').html('اختر مشروعاً لعرض مستنداته');return;}
    try{
      const doc=await frappe.db.get_doc('WAFD Iftar Project',project);
      const site=doc.distribution_site||doc.project_title||'';
      const total=doc.total_meals||doc.planned_distribution_meals||0;
      $r.find('.irc-project-meta').html(`<b>${frappe.utils.escape_html(doc.project_title||project)}</b><span>${frappe.utils.escape_html(site)} · ${frappe.format(total,{fieldtype:'Int'})} وجبة</span>`);
    }catch(e){$r.find('.irc-project-meta').html(`<b>${frappe.utils.escape_html(project)}</b>`);}
  }

  function openPrint(doctype,name,format){ frappe.route_options={print_format:format}; frappe.set_route('print',doctype,name); }
  function openList(doctype,filters){ frappe.route_options=filters||{}; frappe.set_route('List',doctype); }

  async function chooseOperation(project,printFormat){
    const ops=await frappe.db.get_list('WAFD Iftar Daily Operation',{filters:{project},fields:['name','operation_date','status','planned_meals'],order_by:'operation_date desc',limit:366});
    if(!ops.length)return frappe.msgprint('لا توجد سجلات يومية لهذا المشروع');
    if(routeOptions.operation&&ops.some(x=>x.name===routeOptions.operation))return openPrint('WAFD Iftar Daily Operation',routeOptions.operation,printFormat);
    const d=new frappe.ui.Dialog({title:'اختر يوم التشغيل',size:'small',fields:[{fieldtype:'Select',fieldname:'op',label:'السجل اليومي',options:ops.map(x=>`${x.name} — ${x.operation_date||''}`).join('\n'),reqd:1}],primary_action_label:'فتح المعاينة والطباعة',primary_action(v){d.hide();const name=(v.op||'').split(' — ')[0];openPrint('WAFD Iftar Daily Operation',name,printFormat);}});d.show();
  }

  async function openCard(card){
    if(card.type==='page')return frappe.set_route(card.page);
    const project=pc.get_value();
    if(!project)return frappe.msgprint({title:'اختر المشروع',message:'اختر مشروع إفطار صائم أولاً لعرض مستنداته.',indicator:'orange'});
    if(card.type==='project_print')return openPrint('WAFD Iftar Project',project,card.format);
    if(card.type==='operation_print')return chooseOperation(project,card.format);
    if(card.type==='list')return openList(card.doctype,{project});
    if(card.type==='project_form')return frappe.set_route('Form','WAFD Iftar Project',project,card.anchor);
  }

  $section.on('click.wafdReportCenter','.irc-card',function(e){e.preventDefault();const group=$(this).data('group');const idx=Number($(this).data('i'));openCard(group==='p'?primary[idx]:secondary[idx]);});
  $section.on('click.wafdReportCenter','.irc-back',()=>frappe.set_route('wafd-iftar-operations'));
  if(pc.$input)pc.$input.on('change.wafdReportCenter',()=>updateMeta(pc.get_value()));

  if(routeOptions.project){pc.set_value(routeOptions.project);updateMeta(routeOptions.project);}
  else {
    const recent=await frappe.db.get_list('WAFD Iftar Project',{fields:['name'],order_by:'modified desc',limit:1});
    if(recent.length){pc.set_value(recent[0].name);updateMeta(recent[0].name);}
  }
}
