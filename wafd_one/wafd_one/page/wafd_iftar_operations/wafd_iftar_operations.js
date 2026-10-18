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
        <div class="io-tabs"><button type="button" class="active" data-view="today">مشاريع اليوم</button><button type="button" data-view="active">جميع المشاريع النشطة</button></div>
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
    if(currentView==='active'){
      const rows=dashboardData.active_projects||[];
      $r.find('.io-table').html(rows.length?`<div class="table-responsive"><table class="table"><thead><tr><th>المشروع</th><th>الموقع</th><th>البداية</th><th>النهاية</th><th>الوجبات اليومية</th><th>إجمالي الوجبات</th><th>الحالة</th></tr></thead><tbody>${rows.map(p=>`<tr data-project="${frappe.utils.escape_html(p.name)}"><td><b>${frappe.utils.escape_html(p.project_title||p.name)}</b><small>${frappe.utils.escape_html(p.name)}</small></td><td>${frappe.utils.escape_html(p.distribution_site||'')}</td><td>${frappe.utils.escape_html(String(p.start_date||''))}</td><td>${frappe.utils.escape_html(String(p.end_date||''))}</td><td>${num(p.daily_meals)}</td><td>${num(p.total_meals)}</td><td>${frappe.utils.escape_html(p.status||'')}</td></tr>`).join('')}</tbody></table></div>`:`<div class="io-empty"><b>لا توجد مشاريع نشطة</b></div>`);
      return;
    }
    const rows=dashboardData.rows||[];
    $r.find('.io-table').html(rows.length?`<div class="table-responsive"><table class="table"><thead><tr><th>المشروع</th><th>الموقع</th><th>المخطط</th><th>الإنتاج</th><th>التغليف</th><th>التحميل</th><th>التسليم</th><th>الاستلام</th><th>الإنجاز</th></tr></thead><tbody>${rows.map(r=>`<tr data-op="${frappe.utils.escape_html(r.name)}"><td><b>${frappe.utils.escape_html(r.project_title||r.project)}</b><small>${frappe.utils.escape_html(r.project)}</small></td><td>${frappe.utils.escape_html(r.distribution_site||'')}</td><td>${num(r.planned_meals)}</td><td>${num(r.produced_meals)}</td><td>${num(r.packaged_meals)}</td><td>${num(r.loaded_meals)}</td><td>${num(r.delivered_meals)}</td><td>${num(r.received_meals)}</td><td><div class="progress"><div class="progress-bar" style="width:${r.completion_percent||0}%"></div></div><b>${r.completion_percent||0}%</b></td></tr>`).join('')}</tbody></table></div>`:`<div class="io-empty"><b>لا توجد عمليات لهذا التاريخ</b><span>يمكنك عرض جميع المشاريع النشطة من التبويب أعلاه.</span></div>`);
  }

  async function load(allowJump=true){
    const selected=$r.find('.io-date').val();
    const response=await frappe.call({method:'wafd_one.wafd_one.iftar_pro.get_dashboard',args:{date:selected}});
    const x=response.message||{summary:{},rows:[],active_projects:[]};
    dashboardData=x;
    if(allowJump&&!x.rows.length&&x.suggested_date&&!autoJumped){
      autoJumped=true;
      $r.find('.io-date').val(x.suggested_date);
      $r.find('.io-note').html(`<div class="alert alert-info">لا توجد عمليات في تاريخ اليوم؛ تم عرض أقرب يوم تشغيل تلقائياً. ويمكنك دائماً فتح تبويب جميع المشاريع النشطة.</div>`);
      return load(false);
    }
    const s=x.summary||{};
    const cards=[
      ['المشاريع النشطة',s.active_project_count,'briefcase'],['مشاريع اليوم',s.project_count,'calendar'],['الوجبات المطلوبة',s.planned_meals,'food'],
      ['تم الإنتاج',s.produced_meals,'factory'],['تم التغليف',s.packaged_meals,'package'],['تم التحميل',s.loaded_meals,'truck'],
      ['تم التسليم',s.delivered_meals,'delivery'],['تم الاستلام',s.received_meals,'check'],['المتبقي',s.remaining_meals,'remaining'],['نسبة الإنجاز',`${s.completion_percent||0}%`,'percent']
    ];
    $r.find('.io-kpis').html(cards.map(c=>`<div class="io-kpi"><span>${c[0]}</span><strong>${typeof c[1]==='number'?num(c[1]):c[1]}</strong><i class="io-dot"></i></div>`).join(''));
    renderTable();
  }
  load(true);
  const refreshTimer=setInterval(()=>{if(!document.hidden)load(false);},15000);
  $(wrapper).on('remove',()=>clearInterval(refreshTimer));
};
