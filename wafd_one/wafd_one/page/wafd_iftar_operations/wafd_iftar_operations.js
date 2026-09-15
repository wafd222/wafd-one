frappe.pages["wafd-iftar-operations"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("تشغيل إفطار الصائم"), single_column: true });
  const $r = $(wrapper).find(".layout-main-section").attr("dir", "rtl").html(`
    <div class="io-wrap">
      <section class="io-hero">
        <div class="io-hero-overlay"></div>
        <div class="io-brand">
          <img src="/assets/wafd_one/images/wafd-almadinah-official.png" alt="شعار وفد المدينة">
          <div><span>شركة وفد المدينة لخدمات الإعاشة</span><strong>مشروع إفطار صائم</strong><small>لوحة القيادة والتشغيل اليومي</small></div>
        </div>
        <div class="io-controls"><input type="date" class="form-control io-date"><button class="btn btn-light io-new">+ مشروع جديد</button></div>
      </section>
      <div class="io-note"></div>
      <div class="io-kpis"></div>
      <div class="io-card">
        <div class="io-head"><div><h3>المشاريع</h3><p>افصل بين مشاريع التاريخ المحدد وجميع المشاريع النشطة</p></div><button class="btn btn-default io-refresh">تحديث</button></div>
        <div class="io-tabs"><button type="button" class="active" data-view="today">مشاريع اليوم</button><button type="button" data-view="deliveries">عمليات التوصيل</button><button type="button" data-view="active">جميع المشاريع النشطة</button></div>
        <div class="io-table"></div>
      </div>
    </div>`);
  $r.find(".io-date").val(frappe.datetime.get_today());
  let dashboardData={summary:{},rows:[],active_projects:[]};
  let currentView='today';
  let autoJumped=false;

  $r.find('.io-new').get(0).addEventListener('click',()=>{
    sessionStorage.removeItem('wafd_iftar_wizard_draft');
    frappe.route_options={fresh:Date.now()};
    frappe.set_route('wafd-iftar-wizard');
  });
  $r.find('.io-refresh').get(0).addEventListener('click',()=>load(false));
  $r.find('.io-date').get(0).addEventListener('change',()=>load(false));
  $r.find('.io-tabs').on('click','button',function(){currentView=$(this).data('view');$r.find('.io-tabs button').removeClass('active');$(this).addClass('active');renderTable();});
  $r.on('click','[data-op]',function(){frappe.set_route('Form','WAFD Iftar Daily Operation',$(this).data('op'));});
  $r.on('click','[data-project]',function(){frappe.set_route('Form','WAFD Iftar Project',$(this).data('project'));});
  const num=v=>frappe.format(Number(v||0),{fieldtype:'Int'});

  function renderTable(){
    const mobile=window.matchMedia&&window.matchMedia('(max-width: 640px)').matches;
    if(currentView==='deliveries'){
      const rows=dashboardData.iftar_deliveries||[];
      if(mobile){$r.find('.io-table').html(rows.length?`<div class="io-mobile-list">${rows.map(x=>`<article><span class="io-link-badge ${x.contract?'is-contract':'is-standalone'}">${x.contract?'بعقد':'بدون عقد'}</span><b>${frappe.utils.escape_html(x.contract_title||x.iftar_project_title||x.name)}</b><dl><dt>الموقع</dt><dd>${frappe.utils.escape_html(x.destination_name||'')}</dd><dt>السائق</dt><dd>${frappe.utils.escape_html(x.driver||'—')}</dd><dt>الكمية / الموثق</dt><dd>${num(x.quantity)} / ${num(x.verified_quantity)}</dd><dt>الحالة</dt><dd>${frappe.utils.escape_html(x.proof?'تم التسليم':x.status||'')}</dd></dl></article>`).join('')}</div>`:`<div class="io-empty"><b>لا توجد عمليات توصيل إفطار صائم لهذا التاريخ</b><span>تظهر هنا تلقائياً من جدول التوصيل الحالي للسائقين.</span></div>`);return;}
      $r.find('.io-table').html(rows.length?`<div class="table-responsive"><table class="table"><thead><tr><th>التصنيف</th><th>العقد أو العملية</th><th>الموقع</th><th>السائق</th><th>الكمية</th><th>الموثق</th><th>الوقت</th><th>الحالة</th><th>الصورة</th></tr></thead><tbody>${rows.map(x=>`<tr><td><span class="io-link-badge ${x.contract?'is-contract':'is-standalone'}">${frappe.utils.escape_html(x.contract?'بعقد':'بدون عقد')}</span></td><td><b>${frappe.utils.escape_html(x.contract_title||x.iftar_project_title||x.name)}</b><small>${frappe.utils.escape_html(x.contract_number||x.name)}</small></td><td>${x.destination_map_url?`<a href="${frappe.utils.escape_html(x.destination_map_url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(x.destination_name||'فتح الموقع')}</a>`:frappe.utils.escape_html(x.destination_name||'')}</td><td>${frappe.utils.escape_html(x.driver||'')}</td><td>${num(x.quantity)}</td><td>${num(x.verified_quantity)}</td><td>${frappe.utils.escape_html(frappe.datetime.str_to_user(x.planned_arrival)||'')}</td><td>${frappe.utils.escape_html(x.proof?'تم التسليم':x.status||'')}</td><td>${x.proof?.delivery_photo?`<a href="${frappe.utils.escape_html(x.proof.delivery_photo)}" target="_blank"><img class="io-proof-thumb" src="${frappe.utils.escape_html(x.proof.delivery_photo)}"></a>`:'—'}</td></tr>`).join('')}</tbody></table></div>`:`<div class="io-empty"><b>لا توجد عمليات توصيل إفطار صائم لهذا التاريخ</b><span>تظهر هنا تلقائياً عمليات إفطار الصائم المسجلة في جدول التوصيل الحالي للسائقين.</span></div>`);
      return;
    }
    if(currentView==='active'){
      const rows=dashboardData.active_projects||[];
      if(mobile){$r.find('.io-table').html(rows.length?`<div class="io-mobile-list">${rows.map(p=>`<article data-project="${frappe.utils.escape_html(p.name)}"><span class="io-link-badge ${p.contract?'is-contract':'is-standalone'}">${p.contract?'بعقد':'بدون عقد'}</span><b>${frappe.utils.escape_html(p.project_title||p.name)}</b><dl><dt>الموقع</dt><dd>${frappe.utils.escape_html(p.distribution_site||'')}</dd><dt>الفترة</dt><dd>${frappe.utils.escape_html(String(p.start_date||''))} — ${frappe.utils.escape_html(String(p.end_date||''))}</dd><dt>اليومي / الإجمالي</dt><dd>${num(p.daily_meals)} / ${num(p.total_meals)}</dd><dt>الحالة</dt><dd>${frappe.utils.escape_html(p.status||'')}</dd></dl></article>`).join('')}</div>`:`<div class="io-empty"><b>لا توجد مشاريع نشطة</b></div>`);return;}
      $r.find('.io-table').html(rows.length?`<div class="table-responsive"><table class="table"><thead><tr><th>المشروع</th><th>الربط</th><th>الموقع</th><th>البداية</th><th>النهاية</th><th>الوجبات اليومية</th><th>إجمالي الوجبات</th><th>الحالة</th></tr></thead><tbody>${rows.map(p=>`<tr data-project="${frappe.utils.escape_html(p.name)}"><td><b>${frappe.utils.escape_html(p.project_title||p.name)}</b><small>${frappe.utils.escape_html(p.name)}</small></td><td><span class="io-link-badge ${p.contract?'is-contract':'is-standalone'}">${p.contract?'بعقد':'بدون عقد'}</span></td><td>${frappe.utils.escape_html(p.distribution_site||'')}</td><td>${frappe.utils.escape_html(String(p.start_date||''))}</td><td>${frappe.utils.escape_html(String(p.end_date||''))}</td><td>${num(p.daily_meals)}</td><td>${num(p.total_meals)}</td><td>${frappe.utils.escape_html(p.status||'')}</td></tr>`).join('')}</tbody></table></div>`:`<div class="io-empty"><b>لا توجد مشاريع نشطة</b></div>`);
      return;
    }
    const rows=dashboardData.rows||[];
    if(mobile){$r.find('.io-table').html(rows.length?`<div class="io-mobile-list">${rows.map(r=>`<article data-op="${frappe.utils.escape_html(r.name)}"><b>${frappe.utils.escape_html(r.project_title||r.project)}</b><small>${frappe.utils.escape_html(r.distribution_site||'')}</small><dl><dt>المخطط</dt><dd>${num(r.planned_meals)}</dd><dt>الإنتاج / التغليف</dt><dd>${num(r.produced_meals)} / ${num(r.packaged_meals)}</dd><dt>التحميل / موثق السائق</dt><dd>${num(r.loaded_meals)} / ${num(r.driver_verified_meals)}</dd><dt>الاستلام</dt><dd>${num(r.received_meals)} — ${r.completion_percent||0}%</dd></dl></article>`).join('')}</div>`:`<div class="io-empty"><b>لا توجد عمليات لهذا التاريخ</b></div>`);return;}
    $r.find('.io-table').html(rows.length?`<div class="table-responsive"><table class="table"><thead><tr><th>المشروع</th><th>الموقع</th><th>المخطط</th><th>الإنتاج</th><th>التغليف</th><th>التحميل</th><th>التسليم التشغيلي</th><th>توثيق السائق</th><th>الاستلام</th><th>الإنجاز</th></tr></thead><tbody>${rows.map(r=>`<tr data-op="${frappe.utils.escape_html(r.name)}"><td><b>${frappe.utils.escape_html(r.project_title||r.project)}</b><small>${frappe.utils.escape_html(r.project)}</small></td><td>${frappe.utils.escape_html(r.distribution_site||'')}</td><td>${num(r.planned_meals)}</td><td>${num(r.produced_meals)}</td><td>${num(r.packaged_meals)}</td><td>${num(r.loaded_meals)}</td><td>${num(r.delivered_meals)}</td><td><b>${num(r.driver_verified_meals)}</b><small>${num(r.driver_trip_count)} رحلة</small></td><td>${num(r.received_meals)}</td><td><div class="progress"><div class="progress-bar" style="width:${r.completion_percent||0}%"></div></div><b>${r.completion_percent||0}%</b></td></tr>`).join('')}</tbody></table></div>`:`<div class="io-empty"><b>لا توجد عمليات لهذا التاريخ</b><span>يمكنك عرض جميع المشاريع النشطة من التبويب أعلاه.</span></div>`);
  }

  async function load(allowJump=true){
    const selected=$r.find('.io-date').val();
    const response=await frappe.call({method:'wafd_one.wafd_one.iftar_pro.get_dashboard',args:{date:selected}});
    const x=response.message||{summary:{},rows:[],active_projects:[]};
    dashboardData=x;
    if(allowJump&&!x.rows.length&&!(x.iftar_deliveries||[]).length&&x.suggested_date&&!autoJumped){
      autoJumped=true;
      $r.find('.io-date').val(x.suggested_date);
      $r.find('.io-note').html(`<div class="alert alert-info">لا توجد عمليات في تاريخ اليوم؛ تم عرض أقرب يوم تشغيل تلقائياً. ويمكنك دائماً فتح تبويب جميع المشاريع النشطة.</div>`);
      return load(false);
    }
    const s=x.summary||{};
    const cards=[
      ['المشاريع النشطة',s.active_project_count,'briefcase'],['مشاريع اليوم',s.project_count,'calendar'],['الوجبات المطلوبة',s.planned_meals,'food'],
      ['تم الإنتاج',s.produced_meals,'factory'],['تم التغليف',s.packaged_meals,'package'],['تم التحميل',s.loaded_meals,'truck'],
      ['تم التسليم',s.delivered_meals,'delivery'],['موثق بعقد',s.contract_verified_meals,'contract'],['موثق بدون عقد',s.standalone_verified_meals,'standalone'],['تم الاستلام',s.received_meals,'check'],['المتبقي',s.remaining_meals,'remaining'],['نسبة الإنجاز',`${s.completion_percent||0}%`,'percent']
    ];
    $r.find('.io-kpis').html(cards.map(c=>`<div class="io-kpi"><span>${c[0]}</span><strong>${typeof c[1]==='number'?num(c[1]):c[1]}</strong><i class="io-dot"></i></div>`).join(''));
    renderTable();
  }
  load(true);
  const refreshTimer=setInterval(()=>{if(!document.hidden)load(false);},15000);
  $(wrapper).on('remove',()=>clearInterval(refreshTimer));
};
