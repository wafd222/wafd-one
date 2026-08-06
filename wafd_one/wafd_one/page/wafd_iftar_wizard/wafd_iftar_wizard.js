frappe.pages["wafd-iftar-wizard"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({parent: wrapper, title: __("إنشاء مشروع إفطار صائم"), single_column: true});
  wrapper.wafd_iftar_build = () => build_wizard(wrapper);
  wrapper.wafd_iftar_build();
};

frappe.pages["wafd-iftar-wizard"].on_page_show = function(wrapper) {
  if (wrapper.wafd_iftar_build) wrapper.wafd_iftar_build();
};

function build_wizard(wrapper) {
  sessionStorage.removeItem("wafd_iftar_wizard_draft");
  const $root = $(wrapper).find(".layout-main-section").attr("dir", "rtl").empty().html(`
    <div class="iftar-wizard">
      <section class="iw-hero">
        <div><span>WAFD IFTAR PRO</span><h2>إنشاء مشروع إفطار صائم</h2><p>أربع خطوات واضحة من البيانات حتى بدء التشغيل اليومي.</p></div>
        <div class="iw-steps">${[1,2,3,4].map((n,i)=>`<b data-step="${n}" class="${i===0?'active':''}">${n}</b>${i<3?'<i></i>':''}`).join('')}</div>
      </section>
      <section class="iw-card">
        <div class="iw-step-title"></div>
        <div class="iw-grid"></div>
        <div class="iw-summary"></div>
        <div class="iw-actions"><button type="button" class="btn btn-default iw-prev">السابق</button><button type="button" class="btn btn-primary iw-next">التالي</button><button type="button" class="btn btn-primary iw-create">إنشاء المشروع وبدء التشغيل</button></div>
      </section>
    </div>`);

  const definitions = [
    {step:1, fieldtype:'Select', fieldname:'project_title', label:'الموقع الرئيسي', options:`المسجد النبوي الشريف / Prophet’s Mosque\nمسجد قباء / Quba Mosque\nمسجد القبلتين / Qiblatain Mosque\nمسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)\nمشروع أو موقع آخر / Other Project or Site`, reqd:1, default:'المسجد النبوي الشريف / Prophet’s Mosque'},
    {step:1, fieldtype:'Data', fieldname:'contracting_entity', label:'الجهة المتعاقدة', reqd:1, default:'الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي'},
    {step:1, fieldtype:'Select', fieldname:'distribution_site', label:'موقع التوزيع', options:`المسجد النبوي / Prophet Mosque\nمسجد قباء / Quba Mosque\nمسجد القبلتين / Qiblatain Mosque\nالميقات / Miqat\nموقع آخر / Other`, reqd:1, default:'المسجد النبوي / Prophet Mosque'},
    {step:1, fieldtype:'Data', fieldname:'site_details', label:'تفاصيل الموقع أو الباب'},
    {step:2, fieldtype:'Date', fieldname:'start_date', label:'تاريخ البداية', reqd:1, default:frappe.datetime.get_today()},
    {step:2, fieldtype:'Date', fieldname:'end_date', label:'تاريخ النهاية', reqd:1, default:frappe.datetime.get_today()},
    {step:2, fieldtype:'Int', fieldname:'daily_meals', label:'الوجبات اليومية', reqd:1, default:3000},
    {step:2, fieldtype:'Currency', fieldname:'sale_price_per_meal', label:'سعر البيع للوجبة', reqd:1, default:9},
    {step:3, fieldtype:'Select', fieldname:'distribution_type', label:'نوع التوزيع', options:`مسجد أو حرم / Mosque or Haram\nتوزيع خارجي أو جهة / External Distribution or Entity`, default:'مسجد أو حرم / Mosque or Haram', reqd:1},
    {step:3, fieldtype:'Select', fieldname:'meal_template', label:'نوع الوجبة', options:`الوجبة القياسية / Standard Iftar\nوجبة مع زمزم / Iftar + Zamzam\nوجبة مخصصة / Custom Package`, default:'الوجبة القياسية / Standard Iftar', reqd:1},
    {step:3, fieldtype:'Check', fieldname:'include_zamzam', label:'استبدال الماء بزمزم 330 مل'},
    {step:3, fieldtype:'MultiCheck', fieldname:'optional_items', label:'إضافات الوجبة المخصصة', options:[
      {label:'معمول',value:'معمول'}, {label:'فواكه مجففة',value:'فواكه مجففة'}, {label:'مكسرات مشكلة',value:'مكسرات مشكلة'},
      {label:'لوزين',value:'لوزين'}, {label:'عصير برتقال 200 مل',value:'عصير برتقال 200 مل'}, {label:'عصير تفاح 200 مل',value:'عصير تفاح 200 مل'}
    ]},
    {step:4, fieldtype:'Currency', fieldname:'carton_unit_cost', label:'تكلفة الكرتون الواحد (25 وجبة)', default:0},
    {step:4, fieldtype:'Currency', fieldname:'tablecloth_unit_cost', label:'تكلفة السفرة الواحدة', default:0},
    {step:4, fieldtype:'Currency', fieldname:'supervisors_manager_cost', label:'تكلفة مدير المشرفين', default:0},
    {step:4, fieldtype:'Currency', fieldname:'supervisors_cost', label:'إجمالي تكلفة المشرفين', default:0},
    {step:4, fieldtype:'Currency', fieldname:'assistants_cost', label:'إجمالي تكلفة المساعدين', default:0},
    {step:4, fieldtype:'Currency', fieldname:'packaging_workers_cost', label:'تكلفة عمال التغليف', default:0},
    {step:4, fieldtype:'Currency', fieldname:'loading_workers_cost', label:'تكلفة عمال التحميل', default:0},
    {step:4, fieldtype:'Currency', fieldname:'drivers_cost', label:'تكلفة السائقين والمركبات', default:0}
  ];

  const controls = {};
  definitions.forEach(df => {
    const box = $(`<div class="iw-field" data-field-step="${df.step}"></div>`).appendTo($root.find('.iw-grid'));
    controls[df.fieldname] = frappe.ui.form.make_control({parent: box, df, render_input: true});
    controls[df.fieldname].set_value(df.default ?? '');
  });

  const locationDefaults = {
    "المسجد النبوي الشريف / Prophet’s Mosque": ["المسجد النبوي / Prophet Mosque", "الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي"],
    "مسجد قباء / Quba Mosque": ["مسجد قباء / Quba Mosque", "هيئة تطوير منطقة المدينة المنورة"],
    "مسجد القبلتين / Qiblatain Mosque": ["مسجد القبلتين / Qiblatain Mosque", "هيئة تطوير منطقة المدينة المنورة"],
    "مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)": ["الميقات / Miqat", "هيئة تطوير منطقة المدينة المنورة"]
  };
  const titles = {1:'1. بيانات الجهة والموقع',2:'2. المدة والكميات والسعر',3:'3. مكونات الوجبة وطريقة التوزيع',4:'4. التكاليف التشغيلية والمراجعة'};
  let currentStep = 1;
  const value = name => controls[name].get_value();
  const collect = () => { const out={contracting_entity_type:'جهة حكومية / Government Entity'}; Object.keys(controls).forEach(k=>out[k]=controls[k].get_value()); return out; };

  function totals() {
    const start=value('start_date'), end=value('end_date'), daily=Number(value('daily_meals')||0), sale=Number(value('sale_price_per_meal')||0);
    const days=(start&&end)?Math.max(0,frappe.datetime.get_day_diff(end,start)+1):0;
    const meals=days*daily, cartons=Math.ceil(meals/25);
    const operating=['carton_unit_cost','tablecloth_unit_cost','supervisors_manager_cost','supervisors_cost','assistants_cost','packaging_workers_cost','loading_workers_cost','drivers_cost'].reduce((a,k)=>a+Number(value(k)||0),0);
    return {days,meals,cartons,revenue:meals*sale,operating};
  }
  function renderSummary() {
    const t=totals();
    $root.find('.iw-summary').html(`<div><span>عدد الأيام</span><strong>${t.days}</strong></div><div><span>إجمالي الوجبات</span><strong>${frappe.format(t.meals,{fieldtype:'Int'})}</strong></div><div><span>عدد الكراتين المتوقع</span><strong>${frappe.format(t.cartons,{fieldtype:'Int'})}</strong></div><div><span>الإيراد المتوقع</span><strong>${format_currency(t.revenue,'SAR')}</strong></div>`);
  }
  function showStep(step) {
    currentStep=Math.max(1,Math.min(4,step));
    $root.find('[data-field-step]').hide().filter(`[data-field-step="${currentStep}"]`).show();
    $root.find('.iw-step-title').text(titles[currentStep]);
    $root.find('.iw-steps b').removeClass('active done').each(function(){const n=Number($(this).data('step')); if(n===currentStep)$(this).addClass('active'); else if(n<currentStep)$(this).addClass('done');});
    $root.find('.iw-prev').toggle(currentStep>1);
    $root.find('.iw-next').toggle(currentStep<4);
    $root.find('.iw-create').toggle(currentStep===4);
    $root.find('.iw-summary').toggle(currentStep>=2);
    renderSummary();
    window.scrollTo({top:0,behavior:'smooth'});
  }
  function validateStep(step) {
    const missing=definitions.filter(f=>f.step===step&&f.reqd&&!value(f.fieldname));
    if(missing.length){frappe.msgprint(`أكمل الحقول المطلوبة: ${missing.map(x=>x.label).join('، ')}`);return false;}
    if(step===2&&value('end_date')<value('start_date')){frappe.msgprint('تاريخ النهاية يجب ألا يسبق تاريخ البداية');return false;}
    return true;
  }

  Object.values(controls).forEach(c=>{ if(c.$input)c.$input.on('change input',renderSummary); });
  controls.project_title.$input.on('change',()=>{const x=locationDefaults[value('project_title')];if(x){controls.distribution_site.set_value(x[0]);controls.contracting_entity.set_value(x[1]);}});
  controls.meal_template.$input.on('change',()=>{if(value('meal_template')==='وجبة مع زمزم / Iftar + Zamzam')controls.include_zamzam.set_value(1);});
  $root.off('.iftarWizard');
  $root.on('click.iftarWizard','.iw-next',function(e){e.preventDefault();e.stopPropagation();if(validateStep(currentStep))showStep(currentStep+1);});
  $root.on('click.iftarWizard','.iw-prev',function(e){e.preventDefault();e.stopPropagation();showStep(currentStep-1);});
  $root.on('click.iftarWizard','.iw-steps b',function(e){e.preventDefault();const target=Number($(this).data('step'));if(target<currentStep||validateStep(currentStep))showStep(target);});
  let creating=false;
  $root.on('click.iftarWizard','.iw-create',async function(e){
    e.preventDefault();e.stopPropagation();
    if(creating||!validateStep(4)) return;
    creating=true; const $button=$(this).prop('disabled',true);
    try {
      const data=collect();
      if(data.meal_template==='وجبة مع زمزم / Iftar + Zamzam')data.include_zamzam=1;
      const response=await frappe.call({method:'wafd_one.wafd_one.iftar_pro.create_project',args:{data},freeze:true,freeze_message:'جارٍ إنشاء المشروع والخطة اليومية...'});
      sessionStorage.removeItem('wafd_iftar_wizard_draft');
      Object.values(controls).forEach(c=>c.set_value(c.df.default ?? ''));
      showStep(1);
      frappe.show_alert({message:'تم إنشاء المشروع وفتح أول يوم تشغيل',indicator:'green'},5);
      const target=response.message.first_operation?['Form','WAFD Iftar Daily Operation',response.message.first_operation]:['Form','WAFD Iftar Project',response.message.name];
      frappe.set_route(...target);
    } catch(err) {
      console.error(err); frappe.msgprint({title:'تعذر إنشاء المشروع',message:err.message||'حدث خطأ أثناء إنشاء المشروع',indicator:'red'});
    } finally { creating=false; $button.prop('disabled',false); }
  });
  requestAnimationFrame(()=>showStep(1));
}
