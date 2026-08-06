frappe.pages["wafd-iftar-wizard"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({parent:wrapper,title:__("إنشاء مشروع إفطار صائم"),single_column:true});
  const $r=$(wrapper).find('.layout-main-section').attr('dir','rtl').html(`<div class="iftar-wizard"><div class="iw-hero"><div><span>WAFD IFTAR PRO</span><h2>إنشاء مشروع جديد خلال أقل من دقيقة</h2><p>أدخل البيانات الأساسية فقط، وسينشئ النظام الخطة اليومية تلقائياً.</p></div><div class="iw-steps"><b>1</b><i></i><b>2</b><i></i><b>3</b></div></div><div class="iw-card"><div class="iw-grid"></div><div class="iw-summary"></div><button class="btn btn-primary btn-lg iw-create">إنشاء المشروع والخطة اليومية</button></div></div>`);
  const fields=[
   {fieldtype:'Select',fieldname:'project_title',label:'الموقع الرئيسي',options:`المسجد النبوي الشريف / Prophet’s Mosque
مسجد قباء / Quba Mosque
مسجد القبلتين / Qiblatain Mosque
مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)
مشروع أو موقع آخر / Other Project or Site`,reqd:1,default:'المسجد النبوي الشريف / Prophet’s Mosque'},
   {fieldtype:'Data',fieldname:'contracting_entity',label:'الجهة المتعاقدة',reqd:1,default:'الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي'},
   {fieldtype:'Select',fieldname:'distribution_site',label:'موقع التوزيع',options:`المسجد النبوي / Prophet Mosque
مسجد قباء / Quba Mosque
مسجد القبلتين / Qiblatain Mosque
الميقات / Miqat
موقع آخر / Other`,reqd:1,default:'المسجد النبوي / Prophet Mosque'},
   {fieldtype:'Data',fieldname:'site_details',label:'تفاصيل الموقع أو الباب'},
   {fieldtype:'Date',fieldname:'start_date',label:'تاريخ البداية',reqd:1,default:frappe.datetime.get_today()},
   {fieldtype:'Date',fieldname:'end_date',label:'تاريخ النهاية',reqd:1,default:frappe.datetime.get_today()},
   {fieldtype:'Int',fieldname:'daily_meals',label:'الوجبات اليومية',reqd:1,default:3000},
   {fieldtype:'Select',fieldname:'distribution_type',label:'نوع التوزيع',options:`مسجد أو حرم / Mosque or Haram
توزيع خارجي أو جهة / External Distribution or Entity`,default:'مسجد أو حرم / Mosque or Haram',reqd:1},
   {fieldtype:'Select',fieldname:'meal_template',label:'نوع الوجبة',options:`الوجبة القياسية / Standard Iftar
وجبة مع زمزم / Iftar + Zamzam
وجبة مخصصة / Custom Package`,default:'الوجبة القياسية / Standard Iftar',reqd:1},
   {fieldtype:'Currency',fieldname:'sale_price_per_meal',label:'سعر البيع للوجبة',reqd:1,default:9},
   {fieldtype:'Check',fieldname:'include_zamzam',label:'استبدال الماء بزمزم 330 مل'},
   {fieldtype:'MultiCheck',fieldname:'optional_items',label:'إضافات الوجبة المخصصة',options:[{label:'معمول',value:'معمول'},{label:'فواكه مجففة',value:'فواكه مجففة'},{label:'مكسرات مشكلة',value:'مكسرات مشكلة'},{label:'لوزين',value:'لوزين'},{label:'عصير برتقال 200 مل',value:'عصير برتقال 200 مل'},{label:'عصير تفاح 200 مل',value:'عصير تفاح 200 مل'}]}];
  const controls={}; fields.forEach(df=>{const box=$('<div class="iw-field"></div>').appendTo($r.find('.iw-grid')); controls[df.fieldname]=frappe.ui.form.make_control({parent:box,df,render_input:true}); controls[df.fieldname].set_value(df.default||'');});
  const setup={"المسجد النبوي الشريف / Prophet’s Mosque":["المسجد النبوي / Prophet Mosque","الهيئة العامة للعناية بشؤون المسجد الحرام والمسجد النبوي"],"مسجد قباء / Quba Mosque":["مسجد قباء / Quba Mosque","هيئة تطوير منطقة المدينة المنورة"],"مسجد القبلتين / Qiblatain Mosque":["مسجد القبلتين / Qiblatain Mosque","هيئة تطوير منطقة المدينة المنورة"],"مسجد الميقات (ذي الحليفة) / Miqat Mosque (Dhul Hulayfah)":["الميقات / Miqat","هيئة تطوير منطقة المدينة المنورة"]};
  function val(n){return controls[n].get_value()} function update(){const s=val('start_date'),e=val('end_date'),q=Number(val('daily_meals')||0); let days=0;if(s&&e)days=frappe.datetime.get_day_diff(e,s)+1;const total=Math.max(days,0)*q;$r.find('.iw-summary').html(`<div><span>عدد الأيام</span><strong>${Math.max(days,0)}</strong></div><div><span>إجمالي الوجبات</span><strong>${frappe.format(total,{fieldtype:'Int'})}</strong></div><div><span>الإيراد المتوقع</span><strong>${format_currency(total*Number(val('sale_price_per_meal')||0),'SAR')}</strong></div>`)}
  Object.values(controls).forEach(c=>c.$input.on('change input',update)); controls.project_title.$input.on('change',()=>{const x=setup[val('project_title')];if(x){controls.distribution_site.set_value(x[0]);controls.contracting_entity.set_value(x[1]);}});update();
  $r.on('click','.iw-create',async function(){const data={contracting_entity_type:'جهة حكومية / Government Entity'};for(const k in controls)data[k]=controls[k].get_value();if(data.meal_template==='وجبة مع زمزم / Iftar + Zamzam')data.include_zamzam=1;const missing=fields.filter(f=>f.reqd&&!data[f.fieldname]);if(missing.length){frappe.msgprint('أكمل الحقول المطلوبة');return;}const res=await frappe.call({method:'wafd_one.wafd_one.iftar_pro.create_project',args:{data},freeze:true,freeze_message:'جارٍ إنشاء المشروع والخطة اليومية...'});frappe.show_alert({message:'تم إنشاء المشروع بنجاح',indicator:'green'},5); for(const f of fields){controls[f.fieldname].set_value(f.default||'');} update(); frappe.msgprint({title:'تم الإنشاء',indicator:'green',message:`تم إنشاء المشروع <b>${res.message.name}</b>. <a href="/app/wafd-iftar-project/${res.message.name}">فتح المشروع</a>`});});
};
