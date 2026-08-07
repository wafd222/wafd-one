frappe.pages["wafd-iftar-wizard"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({parent: wrapper, title: __("إنشاء مشروع إفطار صائم"), single_column: true});
  wrapper.wafd_iftar_defaults = null;
  wrapper.wafd_iftar_state = { step: 1, creating: false, build_id: 0 };
};

frappe.pages["wafd-iftar-wizard"].on_page_show = async function(wrapper) {
  sessionStorage.removeItem("wafd_iftar_wizard_draft");
  wrapper.wafd_iftar_state = { step: 1, creating: false, build_id: (wrapper.wafd_iftar_state?.build_id || 0) + 1 };
  try {
    const r = await frappe.call({method: "wafd_one.wafd_one.iftar_pro.get_wizard_defaults"});
    wrapper.wafd_iftar_defaults = r.message || {};
  } catch (e) {
    console.error("Unable to load Iftar wizard defaults", e);
    wrapper.wafd_iftar_defaults = {base_price: 9, locations: {}, optional_prices: {}, zamzam_reference_price: 9};
  }
  build_wizard(wrapper);
};

function build_wizard(wrapper) {
  const state = wrapper.wafd_iftar_state || (wrapper.wafd_iftar_state = {step:1, creating:false, build_id:1});
  const defaults = wrapper.wafd_iftar_defaults || {base_price:9, locations:{}, optional_prices:{}, zamzam_reference_price:9};
  const $section = $(wrapper).find(".layout-main-section").attr("dir", "rtl").empty();

  const $root = $(`<div class="iftar-wizard">
    <section class="iw-hero">
      <div><span>WAFD IFTAR PRO</span><h2>إنشاء مشروع إفطار صائم</h2><p>أربع خطوات واضحة من الموقع حتى بدء التشغيل.</p></div>
      <div class="iw-steps">${[1,2,3,4].map((n,i)=>`<button type="button" data-step="${n}" class="${i===0?'active':''}">${n}</button>${i<3?'<i></i>':''}`).join('')}</div>
    </section>
    <section class="iw-card">
      <div class="iw-step-title"></div>
      <div class="iw-grid"></div>
      <div class="iw-price-note"></div>
      <div class="iw-summary"></div>
      <div class="iw-actions">
        <button type="button" class="btn btn-default iw-prev">السابق</button>
        <button type="button" class="btn btn-primary iw-next">التالي</button>
        <button type="button" class="btn btn-primary iw-create">إنشاء المشروع وبدء التشغيل</button>
      </div>
    </section>
  </div>`).appendTo($section);

  const definitions = [
    {step:1, fieldtype:'Select', fieldname:'season_type', label:'الموسم', options:`رمضان / Ramadan\nالاثنين والخميس / Monday & Thursday\nالأيام البيض / White Days\nالعشر من ذي الحجة / First 10 of Dhul Hijjah\nيوم عرفة / Arafah Day\nعاشوراء / Ashura\nمشروع خاص / Special Project`, reqd:1},
    {step:1, fieldtype:'Select', fieldname:'project_title', label:'الموقع الرئيسي', options:`\nالمسجد النبوي الشريف / Prophet’s Mosque\nمسجد قباء / Quba Mosque\nمسجد القبلتين / Qiblatain Mosque\nمسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)\nمشروع أو موقع آخر / Other Project or Site`, reqd:1},
    {step:1, fieldtype:'Data', fieldname:'contracting_entity', label:'الجهة المتعاقدة', reqd:1},
    {step:1, fieldtype:'Data', fieldname:'distribution_site', label:'موقع التوزيع', reqd:1},
    {step:1, fieldtype:'Data', fieldname:'site_details', label:'تفاصيل الموقع أو الباب'},
    {step:2, fieldtype:'Date', fieldname:'start_date', label:'تاريخ البداية', reqd:1},
    {step:2, fieldtype:'Date', fieldname:'end_date', label:'تاريخ النهاية', reqd:1},
    {step:2, fieldtype:'Int', fieldname:'daily_meals', label:'الوجبات اليومية', reqd:1},
    {step:2, fieldtype:'Currency', fieldname:'sale_price_per_meal', label:'سعر البيع للوجبة', reqd:1, read_only:1},
    {step:3, fieldtype:'Data', fieldname:'distribution_type', label:'نوع التوزيع', reqd:1, read_only:1},
    {step:3, fieldtype:'Select', fieldname:'meal_template', label:'نوع الوجبة', options:`\nالوجبة القياسية / Standard Iftar\nوجبة مع زمزم / Iftar + Zamzam\nوجبة مخصصة / Custom Package`, reqd:1},
    {step:3, fieldtype:'Check', fieldname:'include_zamzam', label:`استبدال الماء العادي بزمزم 330 مل`},
    {step:3, fieldtype:'MultiCheck', fieldname:'optional_items', label:'إضافات الوجبة المخصصة', options:[
      {label:'معمول',value:'معمول'}, {label:'فواكه مجففة',value:'فواكه مجففة'}, {label:'مكسرات مشكلة',value:'مكسرات مشكلة'},
      {label:'لوزين',value:'لوزين'}, {label:'عصير برتقال 200 مل',value:'عصير برتقال 200 مل'}, {label:'عصير تفاح 200 مل',value:'عصير تفاح 200 مل'}
    ]},
    {step:4, fieldtype:'Check', fieldname:'reuse_last_setup', label:'نسخ أصحاب السفر والطاقم من آخر مشروع لنفس الموقع', default:1},
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
    {step:4, fieldtype:'Select', fieldname:'other_cost_basis', label:'التكلفة الإضافية — طريقة الاحتساب', options:`للمشروع / Per Project\nلليوم / Per Day\nللوجبة / Per Meal\nللوحدة / Per Unit`}
  ];

  const controls = {};
  definitions.forEach(df => {
    const box = $(`<div class="iw-field" data-field-step="${df.step}"></div>`).appendTo($root.find('.iw-grid'));
    controls[df.fieldname] = frappe.ui.form.make_control({parent: box, df, render_input: true});
  });
  wrapper.wafd_iftar_controls = controls;

  const value = name => controls[name] ? controls[name].get_value() : null;
  const set = (name, val) => controls[name] && controls[name].set_value(val == null ? '' : val);
  const OPTIONAL_ITEMS = ['معمول','فواكه مجففة','مكسرات مشكلة','لوزين','عصير برتقال 200 مل','عصير تفاح 200 مل'];
  const selectedOptionalItems = () => {
    // Frappe MultiCheck can update its internal value after the native change event.
    // Read the actual checked inputs first so simultaneous add-ons are always priced together.
    const $wrap = controls.optional_items && controls.optional_items.$wrapper;
    if ($wrap && $wrap.length) {
      const picked = [];
      $wrap.find('input[type=checkbox]:checked').each(function(){
        const raw = $(this).val();
        const label = ($(this).closest('label').text() || $(this).parent().text() || '').trim();
        const match = OPTIONAL_ITEMS.find(x => x === raw || label.includes(x));
        if (match && !picked.includes(match)) picked.push(match);
      });
      // If the MultiCheck inputs exist, they are the source of truth even when
      // the last option has just been unchecked. Falling back to get_value() in
      // that exact moment can return Frappe's stale pre-change value and keep a
      // removed add-on in the sale price.
      return picked;
    }
    const v = value('optional_items');
    if (Array.isArray(v)) return v.filter(x=>OPTIONAL_ITEMS.includes(x));
    if (!v) return [];
    if (typeof v === 'string') {
      try { const parsed=JSON.parse(v); return (Array.isArray(parsed)?parsed:[v]).filter(x=>OPTIONAL_ITEMS.includes(x)); }
      catch(e) { return OPTIONAL_ITEMS.filter(x=>v.includes(x)); }
    }
    return [];
  };

  function applyLocationDefaults() {
    const title = value('project_title');
    const d = (defaults.locations || {})[title] || {};
    if (d.distribution_site) set('distribution_site', d.distribution_site);
    else if (title && title !== 'مشروع أو موقع آخر / Other Project or Site') set('distribution_site', title);
    if (d.contracting_entity) set('contracting_entity', d.contracting_entity);
    else if (title === 'مشروع أو موقع آخر / Other Project or Site') set('contracting_entity', '');
    set('distribution_type', d.distribution_type || (title === 'مشروع أو موقع آخر / Other Project or Site' ? 'توزيع خارجي أو جهة / External Distribution or Entity' : 'مسجد أو حرم / Mosque or Haram'));
    const external = title === 'مشروع أو موقع آخر / Other Project or Site';
    controls.distribution_site.df.read_only = external ? 0 : 1;
    controls.distribution_site.refresh();
    controls.contracting_entity.df.read_only = (title === 'المسجد النبوي الشريف / Prophet’s Mosque') ? 1 : 0;
    controls.contracting_entity.refresh();
  }

  function automaticSalePrice() {
    const items = selectedOptionalItems();
    let price = Number(defaults.base_price || 9);
    items.forEach(item => { price += Number((defaults.optional_prices || {})[item] || 0); });
    const zamzam = Number(value('include_zamzam') || 0);
    const waterCost = Number(defaults.water_reference_price || 0);
    const zamzamCost = Number(defaults.zamzam_reference_price || 0);
    // Zamzam replaces the normal 330ml water already included in the 9 SAR standard meal.
    // Therefore add only the price difference, never the full Zamzam bottle price again.
    if (zamzam) price += Math.max(0, zamzamCost - waterCost);
    set('sale_price_per_meal', Number(price.toFixed(2)));
    const additions = items.map(x => `${x}: ${format_currency(Number((defaults.optional_prices||{})[x]||0),'SAR')}`);
    if (zamzam) additions.push(`استبدال الماء بزمزم: +${format_currency(Math.max(0,zamzamCost-waterCost),'SAR')}`);
    $root.find('.iw-price-note').html(`<b>السعر الأساسي للوجبة القياسية: ${format_currency(Number(defaults.base_price||9),'SAR')}</b>${additions.length?`<span> + ${additions.join(' + ')}</span>`:''}`);
    renderSummary();
  }

  function totals() {
    const start=value('start_date'), end=value('end_date'), daily=Number(value('daily_meals')||0), sale=Number(value('sale_price_per_meal')||0);
    const days=(start&&end)?Math.max(0,frappe.datetime.get_day_diff(end,start)+1):0;
    const meals=days*daily, cartons=Math.ceil(meals/25);
    return {days, meals, cartons, revenue:meals*sale};
  }
  function renderSummary() {
    const t=totals();
    const cartonCost=t.cartons*Number(value('carton_unit_cost')||0);
    const days=t.days||1;
    const dailyCosts=[['tablecloth_count','tablecloth_unit_cost'],['supervisors_manager_count','supervisors_manager_rate'],['supervisors_count','supervisors_rate'],['assistants_count','assistants_rate'],['packaging_workers_count','packaging_workers_rate'],['loading_workers_count','loading_workers_rate'],['drivers_count','drivers_rate']].reduce((a,p)=>a+Number(value(p[0])||0)*Number(value(p[1])||0)*days,0);
    const basis=value('other_cost_basis');
    const multiplier=basis==='لليوم / Per Day'?days:basis==='للوجبة / Per Meal'?t.meals:1;
    const other=Number(value('other_cost_quantity')||0)*Number(value('other_cost_rate')||0)*multiplier;
    $root.find('.iw-summary').html(`<div><span>عدد الأيام</span><strong>${t.days}</strong></div><div><span>إجمالي الوجبات</span><strong>${frappe.format(t.meals,{fieldtype:'Int'})}</strong></div><div><span>الكراتين (25 وجبة)</span><strong>${frappe.format(t.cartons,{fieldtype:'Int'})}</strong></div><div><span>سعر البيع</span><strong>${format_currency(Number(value('sale_price_per_meal')||0),'SAR')}</strong></div><div><span>تكاليف تشغيل مدخلة</span><strong>${format_currency(cartonCost+dailyCosts+other,'SAR')}</strong></div><div><span>الإيراد المتوقع</span><strong>${format_currency(t.revenue,'SAR')}</strong></div>`);
  }
  function showStep(step) {
    state.step=Math.max(1,Math.min(4,step));
    $root.find('[data-field-step]').hide().filter(`[data-field-step="${state.step}"]`).show();
    const titles={1:'1. بيانات الجهة والموقع',2:'2. المدة والكميات والسعر',3:'3. مكونات الوجبة وطريقة التوزيع',4:'4. التكاليف التشغيلية والمراجعة'};
    $root.find('.iw-step-title').text(titles[state.step]);
    $root.find('.iw-steps button').removeClass('active done').each(function(){const n=Number($(this).data('step')); if(n===state.step)$(this).addClass('active'); else if(n<state.step)$(this).addClass('done');});
    $root.find('.iw-prev').toggle(state.step>1);
    $root.find('.iw-next').toggle(state.step<4);
    $root.find('.iw-create').toggle(state.step===4);
    $root.find('.iw-summary').toggle(state.step>=2);
    $root.find('.iw-price-note').toggle(state.step===2 || state.step===3);
    renderSummary();
  }
  function validateStep(step) {
    const missing=definitions.filter(f=>f.step===step&&f.reqd&&!value(f.fieldname));
    if(missing.length){frappe.msgprint({title:'بيانات ناقصة',message:`أكمل الحقول المطلوبة: ${missing.map(x=>x.label).join('، ')}`,indicator:'orange'});return false;}
    if(step===2 && value('end_date') < value('start_date')){frappe.msgprint('تاريخ النهاية يجب ألا يسبق تاريخ البداية');return false;}
    if(step===2 && Number(value('daily_meals')||0)<=0){frappe.msgprint('أدخل عدد الوجبات اليومية');return false;}
    return true;
  }
  function collect() {
    const out={contracting_entity_type:'جهة حكومية / Government Entity'};
    Object.keys(controls).forEach(k=>out[k]=controls[k].get_value());
    out.optional_items = selectedOptionalItems();
    return out;
  }

  // Clean initial state. These values are intentional defaults, never remnants from a previous project.
  Object.entries(controls).forEach(([name,c]) => {
    try { c.set_value(c.df.fieldtype === 'Check' ? 0 : (['Int','Float','Currency'].includes(c.df.fieldtype) ? 0 : '')); } catch(e) {}
  });
  set('start_date', frappe.datetime.get_today());
  set('end_date', frappe.datetime.get_today());
  set('sale_price_per_meal', Number(defaults.base_price || 9));
  set('other_cost_basis', 'للمشروع / Per Project');
  set('season_type', 'رمضان / Ramadan');
  set('reuse_last_setup', 1);

  // Direct listeners: no delegated click handlers. This prevents lost button events after Frappe page re-renders.
  const nextButton = $root.find('.iw-next').get(0);
  const prevButton = $root.find('.iw-prev').get(0);
  const createButton = $root.find('.iw-create').get(0);
  nextButton.addEventListener('click', e => { e.preventDefault(); if(validateStep(state.step)) showStep(state.step+1); });
  prevButton.addEventListener('click', e => { e.preventDefault(); showStep(state.step-1); });
  $root.find('.iw-steps button').each(function(){ this.addEventListener('click', e => { e.preventDefault(); const target=Number(this.dataset.step); if(target<state.step || validateStep(state.step)) showStep(target); }); });
  createButton.addEventListener('click', async e => {
    e.preventDefault();
    if(state.creating || !validateStep(4)) return;
    state.creating=true;
    createButton.disabled=true; createButton.textContent='جارٍ إنشاء المشروع...';
    try {
      const data=collect();
      if(data.meal_template==='وجبة مع زمزم / Iftar + Zamzam') data.include_zamzam=1;
      const response=await frappe.call({method:'wafd_one.wafd_one.iftar_pro.create_project',args:{data},freeze:true,freeze_message:'جارٍ إنشاء المشروع والخطة اليومية...'});
      sessionStorage.removeItem('wafd_iftar_wizard_draft');
      frappe.show_alert({message:'تم إنشاء المشروع بنجاح — فتح أول يوم تشغيل',indicator:'green'},5);
      const msg=response.message||{};
      if(msg.first_operation) frappe.set_route('Form','WAFD Iftar Daily Operation',msg.first_operation);
      else if(msg.name) frappe.set_route('Form','WAFD Iftar Project',msg.name);
      else frappe.set_route('wafd-iftar-operations');
    } catch(err) {
      console.error(err);
      frappe.msgprint({title:'تعذر إنشاء المشروع',message:(err?.message||'لم يتم إنشاء المشروع. راجع الرسالة الظاهرة ثم حاول مرة أخرى.'),indicator:'red'});
    } finally {
      state.creating=false; createButton.disabled=false; createButton.textContent='إنشاء المشروع وبدء التشغيل';
    }
  });

  // Control listeners are attached to each actual control wrapper, including MultiCheck inputs.
  Object.values(controls).forEach(c => { if(c.$wrapper) c.$wrapper.on('change input', renderSummary); });
  controls.project_title.$wrapper.on('change', () => { applyLocationDefaults(); automaticSalePrice(); });
  controls.optional_items.$wrapper.on('change', () => setTimeout(automaticSalePrice, 0));
  controls.include_zamzam.$wrapper.on('change', automaticSalePrice);
  controls.meal_template.$wrapper.on('change', () => {
    const meal=value('meal_template');
    if(meal==='وجبة مع زمزم / Iftar + Zamzam') set('include_zamzam',1);
    if(meal==='الوجبة القياسية / Standard Iftar') { set('include_zamzam',0); try { controls.optional_items.set_value([]); } catch(e) {} }
    automaticSalePrice();
  });

  automaticSalePrice();
  showStep(1);
}
