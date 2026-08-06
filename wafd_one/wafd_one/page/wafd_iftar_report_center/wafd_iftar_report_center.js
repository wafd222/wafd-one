frappe.pages['wafd-iftar-report-center'].on_page_load=function(wrapper){
  frappe.ui.make_app_page({parent:wrapper,title:__('مركز تقارير إفطار الصائم'),single_column:true});
  const $r=$(wrapper).find('.layout-main-section').attr('dir','rtl').html(`<div class="irc"><div class="irc-head"><h2>مركز التقارير والطباعة</h2><p>كل مستندات المشروع والتشغيل اليومي في شاشة واحدة.</p></div><div class="irc-select"></div><div class="irc-grid"></div></div>`);
  const pc=frappe.ui.form.make_control({parent:$r.find('.irc-select'),df:{fieldtype:'Link',fieldname:'project',options:'WAFD Iftar Project',label:'المشروع',reqd:1},render_input:true});
  const query=frappe.get_route_options()||{}; if(query.project)pc.set_value(query.project);
  const cards=[
    ['ملخص المشروع','project_print','WAFD Iftar Project Summary'], ['نموذج التسليم والاستلام','operation_print','إفطار صائم — تسليم واستلام يومي'],
    ['كشف المشرف والمساعدين','operation_print','WAFD Iftar Supervisor Receipt'], ['السجلات اليومية','list','WAFD Iftar Daily Operation'],
    ['خطة التوزيع والكراتين','project_form','advanced_tab'], ['التكاليف والربحية','project_form','advanced_tab'],
    ['مكونات الوجبة والتسعير','project_form','advanced_tab'], ['لوحة التشغيل اليومية','page','wafd-iftar-operations']
  ];
  $r.find('.irc-grid').html(cards.map((c,i)=>`<button class="irc-card" data-i="${i}"><b>${c[0]}</b><span>فتح / معاينة / طباعة</span></button>`).join(''));
  async function chooseOperation(project,printFormat){
    const ops=await frappe.db.get_list('WAFD Iftar Daily Operation',{filters:{project},fields:['name','operation_date'],order_by:'operation_date desc',limit:366});
    if(!ops.length)return frappe.msgprint('لا توجد سجلات يومية لهذا المشروع');
    if(query.operation&&ops.some(x=>x.name===query.operation))return frappe.set_route('print','WAFD Iftar Daily Operation',query.operation,{print_format:printFormat});
    const d=new frappe.ui.Dialog({title:'اختر يوم التشغيل',fields:[{fieldtype:'Select',fieldname:'op',label:'السجل اليومي',options:ops.map(x=>`${x.name}`).join('\n'),reqd:1}],primary_action_label:'فتح الطباعة',primary_action(v){d.hide();frappe.set_route('print','WAFD Iftar Daily Operation',v.op,{print_format:printFormat});}});d.show();
  }
  $r.on('click','.irc-card',async function(){const card=cards[$(this).data('i')],project=pc.get_value();if(card[1]==='page')return frappe.set_route(card[2]);if(!project)return frappe.msgprint('اختر المشروع أولاً');if(card[1]==='project_print')return frappe.set_route('print','WAFD Iftar Project',project,{print_format:card[2]});if(card[1]==='operation_print')return chooseOperation(project,card[2]);if(card[1]==='list')return frappe.set_route('List',card[2],{project});if(card[1]==='project_form')return frappe.set_route('Form','WAFD Iftar Project',project,card[2]);});
};