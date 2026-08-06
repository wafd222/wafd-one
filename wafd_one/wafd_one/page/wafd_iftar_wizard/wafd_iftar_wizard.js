frappe.pages["wafd-iftar-wizard"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({parent: wrapper, title: __("إنشاء مشروع إفطار صائم"), single_column: true});
  wrapper.wafd_iftar_build = () => build_wizard(wrapper);
};

frappe.pages["wafd-iftar-wizard"].on_page_show = function(wrapper) {
  // Always rebuild a genuinely fresh wizard. Never reuse values from the previous project.
  sessionStorage.removeItem("wafd_iftar_wizard_draft");
  if (wrapper.wafd_iftar_build) wrapper.wafd_iftar_build();
};

function build_wizard(wrapper) {
  const $section = $(wrapper).find(".layout-main-section");
  $section.off(".wafdIftarWizard").attr("dir", "rtl").empty();
  const $root = $(`<div class="iftar-wizard">
      <section class="iw-hero">
        <div><span>WAFD IFTAR PRO</span><h2>إنشاء مشروع إفطار صائم</h2><p>أربع خطوات متسلسلة. كل مشروع جديد يبدأ بنموذج نظيف.</p></div>
        <div class="iw-steps">${[1,2,3,4].map((n,i)=>`<b data-step="${n}" class="${i===0?'active':''}">${n}</b>${i<3?'<i></i>':''}`).join('')}</div>
      </section>
      <section class="iw-card">
        <div class="iw-step-title"></div>
        <div class="iw-grid"></div>
        <div class="iw-summary"></div>
        <div class="iw-actions">
          <button type="button" class="btn btn-default iw-prev">السابق</button>
          <button type="button" class="btn btn-primary iw-next">التالي</button>
          <button type="button" class="btn btn-primary iw-create">إنشاء المشروع وبدء التشغيل</button>
        </div>
      </section>
    </div>`).appendTo($section);

  const definitions = [
    {step:1, fieldtype:'Select', fieldname:'project_title', label:'الموقع الرئيسي', options:`\nالمسجد النبوي الشريف / Prophet’s Mosque\nمسجد قباء / Quba Mosque\nمسجد القبلتين / Qiblatain Mosque\nمسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)\nمشروع أو موقع آخر / Other Project or Site`, reqd:1},
    {step:1, fieldtype:'Data', fieldname:'contracting_entity', label:'الجهة المتعاقدة', reqd:1},
    {step:1, fieldtype:'Select', fieldname:'distribution_site', label:'موقع التوزيع', options:`\nالمسجد النبوي / Prophet Mosque\nمسجد قباء / Quba Mosque\nمسجد القبلتين / Qiblatain Mosque\nالميقات / Miqat\nموقع آخر / Other`, reqd:1},
    {step:1, fieldtype:'Data', fieldname:'site_details', label:'تفاصيل الموقع أو الباب'},
    {step:2, fieldtype:'Date', fieldname:'start_date', label:'تاريخ البداية', reqd:1},
    {step:2, fieldtype:'Date', fieldname:'end_date', label:'تاريخ النهاية', reqd:1},
    {step:2, fieldtype:'Int', fieldname:'daily_meals', label:'الوجبات اليومية', reqd:1},
    {step:2, fieldtype:'Currency', fieldname:'sale_price_per_meal', label:'سعر البيع للوجبة', reqd:1},
    {step:3, fieldtype:'Select', fieldname:'distribution_type', label:'نوع التوزيع', options:`\nمسجد أو حرم / Mosque or Haram\nتوزيع خارجي أو جهة / External Distribution or Entity`, reqd:1},
    {step:3, fieldtype:'Select', fieldname:'meal_template', label:'نوع الوجبة', options:`\nالوجبة القياسية / Standard Iftar\nوجبة مع زمزم / Iftar + Zamzam\nوجبة مخصصة / Custom Package`, reqd:1},
    {step:3, fieldtype:'Check', fieldname:'include_zamzam', label:'استبدال الماء العادي بزمزم 330 مل (تكلفة مرجعية 9 ر.س)'},
    {step:3, fieldtype:'MultiCheck', fieldname:'optional_items', label:'إضافات الوجبة المخصصة', options:[
      {label:'معمول',value:'معمول'}, {label:'فواكه مجففة',value:'فواكه مجففة'}, {label:'مكسرات مشكلة',value:'مكسرات مشكلة'},
      {label:'لوزين',value:'لوزين'}, {label:'عصير برتقال 200 مل',value:'عصير برتقال 200 مل'}, {label:'عصير تفاح 200 مل',value:'عصير تفاح 200 مل'}
    ]},
    {step:4, fieldtype:'Currency', fieldname:'carton_unit_cost', label:'سعر الكرتون الواحد (25 وجبة)'},
    {step:4, fieldtype:'Int', fieldname:'tablecloth_count', label:'عدد السفر يومياً'},
    {step:4, fieldtype:'Currency', fieldname:'tablecloth_unit_cost', label:'سعر السفرة الواحدة'},
    {step:4, fieldtype:'Int', fieldname:'supervisors_manager_count', label:'عدد مديري المشرفين'},
    {step:4, fieldtype:'Currency', fieldname:'supervisors_manager_rate', label:'أجر مدير المشرفين / يوم'},
    {step:4, fieldtype:'Int', fieldname:'supervisors_count', label:'عدد المشرفين'},
    {step:4, fieldtype:'Currency', fieldname:'supervisors_rate', label:'أجر المشرف الواحد / يوم'},
    {step:4, fieldtype:'Int', fieldname:'assistants_count', label:'عدد المساعدين'},
    {step:4, fieldtype:'Currency', fieldname:'assistants_rate', label:'أجر المساعد الواحد / يوم'},
    {step:4, fieldtype:'Int', fieldname:'packaging_workers_count', label:'عدد عمال التغليف'},
    {step:4, fieldtype:'Currency', fieldname:'packaging_workers_rate', label:'أجر عامل التغليف / يوم'},
    {step:4, fieldtype:'Int', fieldname:'loading_workers_count', label:'عدد عمال التحميل'},
    {step:4, fieldtype:'Currency', fieldname:'loading_workers_rate', label:'أجر عامل التحميل / يوم'},
    {step:4, fieldtype:'Int', fieldname:'drivers_count', label:'عدد السائقين'},
    {step:4, fieldtype:'Currency', fieldname:'drivers_rate', label:'أجر السائق / يوم'},
    {step:4, fieldtype:'Data', fieldname:'other_cost_description', label:'تكلفة إضافية — الوصف'},
    {step:4, fieldtype:'Float', fieldname:'other_cost_quantity', label:'التكلفة الإضافية — الكمية'},
    {step:4, fieldtype:'Currency', fieldname:'other_cost_rate', label:'التكلفة الإضافية — السعر'},
    {step:4, fieldtype:'Select', fieldname:'other_cost_basis', label:'التكلفة الإضافية — طريقة الاحتساب', options:`للمشروع / Per Project
لليوم / Per Day
للوجبة / Per Meal
للوحدة / Per Unit`}
  ];

  const controls = {};
  definitions.forEach(df => {
    const box = $(`<div class="iw-field" data-field-step="${df.step}"></div>`).appendTo($root.find('.iw-grid'));
    controls[df.fieldname] = frappe.ui.form.make_control({parent: box, df, render_input: true});
    controls[df.fieldname].set_value(df.fieldtype === 'Check' ? 0 : (['Int','Float','Currency'].includes(df.fieldtype) ? 0 : ''));
  });

  const locationDefaults = {
    "المسجد النبوي الشريف / Prophet’s Mosque": ["المسجد النبوي / Prophet Mosque", "الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي"],
    "مسجد قباء / Quba Mosque": ["مسجد قباء / Quba Mosque", "هيئة تطوير منطقة المدينة المنورة"],
    "مسجد القبلتين / Qiblatain Mosque": ["مسجد القبلتين / Qiblatain Mosque", "هيئة تطوير منطقة المدينة المنورة"],
    "مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)": ["الميقات / Miqat", "هيئة تطوير منطقة المدينة المنورة"]
  };
  const titles = {1:'1. بيانات الجهة والموقع',2:'2. المدة والكميات والسعر',3:'3. مكونات الوجبة وطريقة التوزيع',4:'4. التكاليف التشغيلية والمراجعة'};
  let currentStep = 1;
  let creating = false;
  const value = name => controls[name] ? controls[name].get_value() : null;
  const collect = () => {
    const out={contracting_entity_type:'جهة حكومية / Government Entity'};
    Object.keys(controls).forEach(k=>out[k]=controls[k].get_value());
    return out;
  };

  function totals() {
    const start=value('start_date'), end=value('end_date'), daily=Number(value('daily_meals')||0), sale=Number(value('sale_price_per_meal')||0);
    const days=(start&&end)?Math.max(0,frappe.datetime.get_day_diff(end,start)+1):0;
    const meals=days*daily, cartons=Math.ceil(meals/25);
    return {days,meals,cartons,revenue:meals*sale};
  }
  function renderSummary() {
    const t=totals();
    const cartonCost=t.cartons*Number(value('carton_unit_cost')||0);
    const days=t.days||1;
    const dailyCosts=[['tablecloth_count','tablecloth_unit_cost'],['supervisors_manager_count','supervisors_manager_rate'],['supervisors_count','supervisors_rate'],['assistants_count','assistants_rate'],['packaging_workers_count','packaging_workers_rate'],['loading_workers_count','loading_workers_rate'],['drivers_count','drivers_rate']].reduce((a,p)=>a+Number(value(p[0])||0)*Number(value(p[1])||0)*days,0);
    const other=Number(value('other_cost_quantity')||0)*Number(value('other_cost_rate')||0)*(value('other_cost_basis')==='لليوم / Per Day'?days:value('other_cost_basis')==='للوجبة / Per Meal'?t.meals:1);
    $root.find('.iw-summary').html(`<div><span>عدد الأيام</span><strong>${t.days}</strong></div><div><span>إجمالي الوجبات</span><strong>${frappe.format(t.meals,{fieldtype:'Int'})}</strong></div><div><span>الكراتين (25 وجبة)</span><strong>${frappe.format(t.cartons,{fieldtype:'Int'})}</strong></div><div><span>تكاليف تشغيل مدخلة</span><strong>${format_currency(cartonCost+dailyCosts+other,'SAR')}</strong></div><div><span>الإيراد المتوقع</span><strong>${format_currency(t.revenue,'SAR')}</strong></div>`);
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
    $root.get(0)?.scrollIntoView({block:'start'});
  }
  function validateStep(step) {
    const missing=definitions.filter(f=>f.step===step&&f.reqd&&!value(f.fieldname));
    if(missing.length){frappe.msgprint({title:'بيانات ناقصة',message:`أكمل الحقول المطلوبة: ${missing.map(x=>x.label).join('، ')}`,indicator:'orange'});return false;}
    if(step===2&&value('end_date')<value('start_date')){frappe.msgprint('تاريخ النهاية يجب ألا يسبق تاريخ البداية');return false;}
    if(step===2&&Number(value('daily_meals')||0)<=0){frappe.msgprint('أدخل عدد الوجبات اليومية');return false;}
    return true;
  }

  Object.values(controls).forEach(c=>{ if(c.$input)c.$input.on('change.wafdIftarWizard input.wafdIftarWizard',renderSummary); });
  controls.project_title.$input.on('change.wafdIftarWizard',()=>{const x=locationDefaults[value('project_title')];if(x){controls.distribution_site.set_value(x[0]);controls.contracting_entity.set_value(x[1]);}});
  controls.meal_template.$input.on('change.wafdIftarWizard',()=>{if(value('meal_template')==='وجبة مع زمزم / Iftar + Zamzam')controls.include_zamzam.set_value(1);});

  $section.on('click.wafdIftarWizard','.iw-next',function(e){e.preventDefault();e.stopPropagation();if(validateStep(currentStep))showStep(currentStep+1);});
  $section.on('click.wafdIftarWizard','.iw-prev',function(e){e.preventDefault();e.stopPropagation();showStep(currentStep-1);});
  $section.on('click.wafdIftarWizard','.iw-steps b',function(e){e.preventDefault();const target=Number($(this).data('step')); if(target<currentStep||validateStep(currentStep))showStep(target);});
  $section.on('click.wafdIftarWizard','.iw-create',async function(e){
    e.preventDefault();e.stopPropagation();
    if(creating || !validateStep(4)) return;
    creating = true;
    const $btn=$(this).prop('disabled',true).text('جارٍ إنشاء المشروع...');
    try {
      const data=collect();
      if(data.meal_template==='وجبة مع زمزم / Iftar + Zamzam')data.include_zamzam=1;
      const response=await frappe.call({method:'wafd_one.wafd_one.iftar_pro.create_project',args:{data},freeze:true,freeze_message:'جارٍ إنشاء المشروع والخطة اليومية...'});
      sessionStorage.removeItem("wafd_iftar_wizard_draft");
      Object.values(controls).forEach(c => { try { c.set_value(c.df.fieldtype === 'Check' ? 0 : (['Int','Float','Currency'].includes(c.df.fieldtype) ? 0 : '')); } catch(e) {} });
      frappe.show_alert({message:'تم إنشاء المشروع بنجاح — فتح أول يوم تشغيل',indicator:'green'},5);
      const msg=response.message||{};
      if(msg.first_operation){frappe.set_route('Form','WAFD Iftar Daily Operation',msg.first_operation);}
      else if(msg.name){frappe.set_route('Form','WAFD Iftar Project',msg.name);}
      else {frappe.set_route('wafd-iftar-operations');}
    } catch (err) {
      console.error(err);
      frappe.msgprint({title:'تعذر إنشاء المشروع',message:'لم يتم إنشاء المشروع. راجع الرسالة الظاهرة ثم صحح البيانات وحاول مرة أخرى.',indicator:'red'});
    } finally {
      creating=false;
      $btn.prop('disabled',false).text('إنشاء المشروع وبدء التشغيل');
    }
  });
  showStep(1);
}
