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
    <div class="irc-head"><div><span>WAFD IFTAR PRO</span><h2>مركز التقارير والطباعة</h2><p>ابحث بالمشروع أو صاحب السفرة أو التاريخ، ثم افتح جميع التقارير من مكان واحد.</p></div><button type="button" class="btn irc-back">لوحة التشغيل اليومية</button></div>
    <div class="irc-search-panel">
      <div class="irc-search-project"></div><div class="irc-search-owner"></div><div class="irc-search-date"></div>
      <button type="button" class="btn btn-primary irc-search-btn">بحث</button><button type="button" class="btn btn-default irc-clear-btn">مسح البحث</button>
    </div>
    <div class="irc-results"></div>
    <div class="irc-toolbar"><div class="irc-project-meta">اختر مشروعاً من نتائج البحث لعرض مستنداته</div></div>
    <div class="irc-section-title">المستندات الأساسية</div><div class="irc-grid irc-primary"></div>
    <div class="irc-section-title">المتابعة والتحليل</div><div class="irc-grid irc-secondary"></div>
  </div>`).appendTo($section);

  const projectControl=frappe.ui.form.make_control({parent:$r.find('.irc-search-project'),df:{fieldtype:'Link',fieldname:'project',options:'WAFD Iftar Project',label:'المشروع',placeholder:'كل المشاريع'},render_input:true});
  const ownerControl=frappe.ui.form.make_control({parent:$r.find('.irc-search-owner'),df:{fieldtype:'Data',fieldname:'table_owner',label:'صاحب السفرة',placeholder:'اكتب اسم صاحب السفرة'},render_input:true});
  const dateControl=frappe.ui.form.make_control({parent:$r.find('.irc-search-date'),df:{fieldtype:'Date',fieldname:'date',label:'التاريخ'},render_input:true});
  const routeOptions=frappe.route_options||{}; frappe.route_options=null;
  let selectedProject='';
  let lastResults=[];

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

  function resultHtml(row){
    const title=frappe.utils.escape_html(row.project_title||row.name);
    const site=frappe.utils.escape_html(row.distribution_site||'');
    const dates=[row.start_date,row.end_date].filter(Boolean).join(' — ');
    return `<button type="button" class="irc-result ${selectedProject===row.name?'selected':''}" data-project="${frappe.utils.escape_html(row.name)}"><b>${title}</b><span>${site}</span><small>${frappe.utils.escape_html(dates)} · ${frappe.format(row.total_meals||row.daily_meals||0,{fieldtype:'Int'})} وجبة</small></button>`;
  }

  async function runSearch(autoSelect=false){
    const response=await frappe.call({method:'wafd_one.wafd_one.iftar_pro.search_iftar_projects',args:{project:projectControl.get_value()||null,table_owner:ownerControl.get_value()||null,date:dateControl.get_value()||null,limit:200},freeze:true,freeze_message:'جارٍ البحث عن المشاريع...'});
    lastResults=response.message||[];
    $r.find('.irc-results').html(lastResults.length?`<div class="irc-results-head"><b>نتائج البحث</b><span>${lastResults.length} مشروع</span></div><div class="irc-result-grid">${lastResults.map(resultHtml).join('')}</div>`:`<div class="irc-no-results">لا توجد مشاريع مطابقة لخيارات البحث.</div>`);
    if(autoSelect && lastResults.length===1) selectProject(lastResults[0].name);
  }

  async function selectProject(project){
    selectedProject=project||'';
    $r.find('.irc-result').removeClass('selected').filter(`[data-project="${CSS.escape(selectedProject)}"]`).addClass('selected');
    if(!selectedProject){$r.find('.irc-project-meta').html('اختر مشروعاً من نتائج البحث لعرض مستنداته');return;}
    const row=lastResults.find(x=>x.name===selectedProject);
    if(row){
      $r.find('.irc-project-meta').html(`<b>${frappe.utils.escape_html(row.project_title||row.name)}</b><span>${frappe.utils.escape_html(row.distribution_site||'')} · ${frappe.format(row.total_meals||row.daily_meals||0,{fieldtype:'Int'})} وجبة</span>`);
      return;
    }
    try{
      const doc=await frappe.db.get_doc('WAFD Iftar Project',selectedProject);
      $r.find('.irc-project-meta').html(`<b>${frappe.utils.escape_html(doc.project_title||selectedProject)}</b><span>${frappe.utils.escape_html(doc.distribution_site||'')} · ${frappe.format(doc.total_meals||doc.daily_meals||0,{fieldtype:'Int'})} وجبة</span>`);
    }catch(e){$r.find('.irc-project-meta').html(`<b>${frappe.utils.escape_html(selectedProject)}</b>`);}
  }

  function openPrint(doctype,name,format){
    // Open the exact mapped Print Format as PDF. This avoids Frappe route_options
    // leaking between cards and guarantees every report card opens its own document.
    const q = new URLSearchParams({doctype, name, format, no_letterhead:'0'});
    window.open('/api/method/frappe.utils.print_format.download_pdf?' + q.toString(), '_blank', 'noopener');
  }
  function openList(doctype,filters){frappe.route_options=filters||{};frappe.set_route('List',doctype);}
  async function chooseOperation(project,printFormat){
    const ops=await frappe.db.get_list('WAFD Iftar Daily Operation',{filters:{project},fields:['name','operation_date','status','planned_meals'],order_by:'operation_date desc',limit:366});
    if(!ops.length)return frappe.msgprint('لا توجد سجلات يومية لهذا المشروع');
    if(routeOptions.operation&&ops.some(x=>x.name===routeOptions.operation))return openPrint('WAFD Iftar Daily Operation',routeOptions.operation,printFormat);
    const d=new frappe.ui.Dialog({title:'اختر يوم التشغيل',size:'small',fields:[{fieldtype:'Select',fieldname:'op',label:'السجل اليومي',options:ops.map(x=>`${x.name} — ${x.operation_date||''}`).join('\n'),reqd:1}],primary_action_label:'فتح المعاينة والطباعة',primary_action(v){d.hide();openPrint('WAFD Iftar Daily Operation',(v.op||'').split(' — ')[0],printFormat);}});d.show();
  }
  async function openCard(card){
    if(card.type==='page')return frappe.set_route(card.page);
    const project=selectedProject;
    if(!project)return frappe.msgprint({title:'اختر المشروع',message:'اختر مشروعاً من نتائج البحث أولاً.',indicator:'orange'});
    if(card.type==='project_print')return openPrint('WAFD Iftar Project',project,card.format);
    if(card.type==='operation_print')return chooseOperation(project,card.format);
    if(card.type==='list')return openList(card.doctype,{project});
    if(card.type==='project_form'){ frappe.set_route('Form','WAFD Iftar Project',project); return; }
  }

  $section.on('click.wafdReportCenter','.irc-search-btn',()=>runSearch(true));
  $section.on('click.wafdReportCenter','.irc-clear-btn',()=>{projectControl.set_value('');ownerControl.set_value('');dateControl.set_value('');selectedProject='';selectProject('');runSearch(false);});
  $section.on('click.wafdReportCenter','.irc-result',function(){selectProject($(this).data('project'));});
  $section.on('click.wafdReportCenter','.irc-card',function(e){e.preventDefault();const group=$(this).data('group');const idx=Number($(this).data('i'));openCard(group==='p'?primary[idx]:secondary[idx]);});
  $section.on('click.wafdReportCenter','.irc-back',()=>frappe.set_route('wafd-iftar-operations'));

  if(routeOptions.project){projectControl.set_value(routeOptions.project);await runSearch(true);}
  else {await runSearch(false);}
}
