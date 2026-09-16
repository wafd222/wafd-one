frappe.pages["wafd-iftar-team"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({parent: wrapper, title: __("إفطار الصائم"), single_column: true});

  const $root = $(wrapper).find(".layout-main-section").html(`
    <div class="ift-simple">
      <header class="ift-head">
        <div><span class="ift-kicker">WAFD ONE</span><h1 class="ift-title">إفطار الصائم</h1><p class="ift-role"></p></div>
        <div class="ift-filters">
          <input type="date" class="form-control ift-date" aria-label="تاريخ التشغيل">
          <button class="btn btn-light ift-refresh">تحديث</button>
        </div>
      </header>
      <main class="ift-content"><div class="ift-loading">جارٍ تحميل الشاشة…</div></main>
    </div>`);

  $root.find(".ift-date").val(frappe.datetime.get_today());
  let data = {projects: [], operations: [], reports: [], mode: ""};
  const esc = value => frappe.utils.escape_html(String(value || ""));
  const num = value => frappe.format(Number(value || 0), {fieldtype: "Int"});
  const time = value => value ? frappe.datetime.str_to_user(value) : "";
  const call = (method, args = {}) => frappe.call({
    method: `wafd_one.wafd_one.iftar_team.${method}`, args, freeze: true
  });
  const upload = (fieldname, label) => ({fieldname, fieldtype: "Attach Image", label, reqd: 1});

  function dialog(title, fields, label, action) {
    const instance = new frappe.ui.Dialog({
      title, fields, primary_action_label: label,
      primary_action: async values => {
        await action(values);
        instance.hide();
        await load();
      }
    });
    instance.show();
  }

  function empty(message = "لا توجد مهمة لك في هذا اليوم") {
    return `<section class="ift-empty"><span>✓</span><h2>${esc(message)}</h2><p>اختر تاريخاً آخر عند الحاجة، أو انتظر إسناد المهمة من الإدارة.</p></section>`;
  }

  function operationForProject(projectName) {
    return (data.operations || []).find(operation => operation.project === projectName) || null;
  }

  function stageStrip(operation, submitted) {
    const stages = [
      ["الإدارة", submitted],
      ["المطبخ", operation && operation.kitchen_ready_approved],
      ["التوصيل", operation && operation.delivery_plan_approved],
      ["الموقع", operation && operation.site_receipt_approved],
      ["التوزيع", operation && operation.site_report_approved],
      ["التقرير", operation && operation.daily_report_sent],
    ];
    return `<div class="ift-stage-strip">${stages.map(([label, done]) => `<span class="${done ? "done" : ""}">${done ? "✓ " : ""}${esc(label)}</span>`).join("")}</div>`;
  }

  function adminView() {
    const projects = data.projects || [];
    return `
      <section class="ift-admin-main">
        <div><b>إدارة المشروع والمهام</b><span>سجل بيانات المشروع والفريق أولاً، ثم اعتمد المشروع مرة واحدة لإظهار مهمة كل مرحلة للموظف المسؤول.</span></div>
        <button class="btn btn-dark" data-page="wafd-iftar-wizard">＋ تسجيل مشروع جديد</button>
      </section>
      <div class="ift-section-title"><h2>المشاريع</h2><span>${num(projects.length)}</span></div>
      ${projects.length ? `<section class="ift-project-list">${projects.map(project => {
        const submitted = Number(project.docstatus) === 1;
        const operation = operationForProject(project.name);
        return `
        <article class="ift-project-card admin-project">
          <div class="ift-card-top"><span class="ift-state ${submitted ? "done" : "waiting"}">${submitted ? "معتمد · المهام ظاهرة للموظفين" : "بانتظار اعتماد الإدارة"}</span><small>${esc(project.name)}</small></div>
          <h3>${esc(project.project_title)}</h3>
          <p>${esc(project.distribution_site)} · ${esc(project.contracting_entity)}</p>
          <div class="ift-numbers">
            <div><b>${num(project.daily_meals)}</b><span>وجبة يومياً</span></div>
            <div><b>${num(project.number_of_days)}</b><span>يوم تشغيل</span></div>
            <div><b>${num(project.supervisors_count)}</b><span>مشرف ميداني</span></div>
          </div>
          ${stageStrip(operation, submitted)}
          <div class="ift-team-summary">
            <span><b>مدير المشروع</b>${esc(project.project_manager_user || "—")}</span>
            <span><b>المطبخ</b>${esc(project.kitchen_supervisor_user || "—")}</span>
            <span><b>التوصيل</b>${esc(project.delivery_supervisor_user || "—")}</span>
            <span><b>الموقع</b>${esc(project.site_manager_user || "—")}</span>
          </div>
          <div class="ift-actions">
            <button class="btn btn-default" data-open-project="${esc(project.name)}">تعديل / مراجعة البيانات</button>
            <button class="btn btn-default" data-supervisors="${esc(project.name)}">المشرفون وأصحاب السفر</button>
            ${!submitted ? `<button class="btn btn-dark" data-activate="${esc(project.name)}">اعتماد المشروع وإظهار المهام للموظفين</button>` : ""}
          </div>
        </article>`;
      }).join("")}</section>` : empty("لا يوجد مشروع مسجل بعد")}
      ${adminReports()}`;
  }

  function adminReports() {
    const ready = (data.operations || []).filter(operation => operation.site_report_approved && !operation.daily_report_sent);
    if (!ready.length) return "";
    return `<div class="ift-section-title"><h2>تقارير جاهزة للإرسال</h2><span>${num(ready.length)}</span></div>
      <section class="ift-project-list">${ready.map(operation => `
        <article class="ift-project-card compact"><span class="ift-state done">جاهز</span><h3>${esc(operation.project_title)}</h3>
        <p>اكتمل تقرير الموقع وأصبح جاهزاً للإرسال للجهة.</p>
        <button class="btn btn-dark ift-primary" data-send="${esc(operation.name)}">اعتماد وإرسال التقرير</button></article>`).join("")}</section>`;
  }

  function projectManagerCard(operation) {
    const supervisorReports = (data.reports || []).filter(report => report.daily_operation === operation.name);
    const completed = supervisorReports.filter(report => report.manager_approved).length;
    return `<article class="ift-task-card manager">
      <div class="ift-card-top"><span class="ift-state">متابعة اليوم</span><small>${esc(operation.project)}</small></div>
      <h2>${esc(operation.project_title)}</h2><p>${esc(operation.distribution_site)}</p>
      <div class="ift-numbers four">
        <div><b>${num(operation.planned_meals)}</b><span>المطلوب</span></div>
        <div><b>${num(operation.kitchen_ready_meals)}</b><span>جاهز</span></div>
        <div><b>${num(operation.loaded_meals)}</b><span>محمل</span></div>
        <div><b>${num(operation.site_received_meals)}</b><span>وصل الموقع</span></div>
      </div>
      <div class="ift-simple-progress"><i style="width:${Math.min(100, Number(operation.completion_percent || 0))}%"></i></div>
      <div class="ift-summary-line"><span>تقارير المشرفين المعتمدة</span><b>${num(completed)} من ${num(supervisorReports.length)}</b></div>
    </article>`;
  }

  function projectManagerView() {
    if (!data.operations.length) return empty();
    return `<section class="ift-task-list">${data.operations.map(projectManagerCard).join("")}</section>`;
  }

  function kitchenCard(operation) {
    if (operation.kitchen_ready_approved) return doneCard(operation, "تم اعتماد مرحلة المطبخ", `${num(operation.kitchen_ready_meals)} وجبة جاهزة ومغلفة`, operation.kitchen_ready_time);
    return `<article class="ift-task-card focus">
      <span class="ift-state working">مهمتك الآن</span>
      <h2>${esc(operation.project_title)}</h2><p>${esc(operation.distribution_site)}</p>
      <div class="ift-big-number"><b>${num(operation.planned_meals)}</b><span>وجبة مطلوبة اليوم</span></div>
      <div class="ift-notice"><span>بعد اكتمال الإنتاج والتغليف سجّل العدد الجاهز واعتمد مرحلتك. بعدها تظهر مهمة التوصيل تلقائياً.</span></div>
      <button class="btn btn-dark ift-primary" data-kitchen="${esc(operation.name)}" data-ready="${operation.kitchen_ready_meals || operation.planned_meals}">اعتماد مرحلة المطبخ</button>
    </article>`;
  }

  function kitchenView() {
    if (!data.operations.length) return empty();
    return `<section class="ift-task-list">${data.operations.map(kitchenCard).join("")}</section>`;
  }

  function deliveryCard(operation) {
    if (!operation.kitchen_ready_approved) return waitingCard(operation, "بانتظار جاهزية المطبخ", "تم إسناد مهمة التوصيل لك. ستصبح قابلة للتنفيذ تلقائياً بعد اعتماد المطبخ.");
    if (operation.delivery_plan_approved) return doneCard(operation, "تم اعتماد التحميل والتوجيه", `${num(operation.loaded_meals)} وجبة موزعة على السيارات`, operation.delivery_plan_approved_at);
    const trips = operation.deliveries || [];
    return `<article class="ift-task-card focus"><span class="ift-state working">مهمتك الآن</span>
      <h2>توزيع السيارات</h2><p>${esc(operation.project_title)} · ${num(operation.kitchen_ready_meals)} وجبة جاهزة</p>
      ${trips.length ? `<div class="ift-vehicle-list">${trips.map(trip => `<button data-trip="${esc(trip.name)}" data-bread="${trip.iftar_bread_quantity || 0}"><b>${esc(trip.driver || "اختر السائق")} · ${esc(trip.vehicle || "اختر السيارة")}</b><span>${esc(trip.destination_name || "حدد الموقع")} · ${num(trip.quantity)} وجبة · ${num(trip.iftar_bread_quantity)} خبز</span></button>`).join("")}</div>` : `<div class="ift-notice"><b>لم تُربط سيارات بعد</b><span>استخدم جدول التوصيل الحالي؛ لن ينشئ النظام رحلة مكررة.</span></div>`}
      <div class="ift-actions stacked"><button class="btn btn-default" data-page="wafd-delivery-supervisor">فتح جدول التوصيل</button>${trips.length ? `<button class="btn btn-dark" data-dispatch="${esc(operation.name)}">اعتماد التحميل والتوجيه</button>` : ""}</div>
    </article>`;
  }

  function deliveryView() {
    if (!data.operations.length) return empty();
    return `<section class="ift-task-list">${data.operations.map(deliveryCard).join("")}</section>`;
  }

  function siteView() {
    if (!data.operations.length) return empty();
    return `<section class="ift-task-list">${data.operations.map(operation => siteOperation(operation)).join("")}</section>${siteReports()}`;
  }

  function siteOperation(operation) {
    const reports = (data.reports || []).filter(report => report.daily_operation === operation.name);
    if (operation.site_report_approved) return doneCard(operation, "تم إرسال تقرير الموقع للإدارة", "اكتمل عمل الموقع لهذا اليوم", operation.site_report_approved_at);
    if (!operation.delivery_plan_approved) return waitingCard(operation, "بانتظار التوصيل", "تم إسناد مهمة الموقع لك. ستظهر بيانات السيارات والسائقين بعد اعتماد مشرف التوصيل.");
    if (!Number(operation.delivery_verified_meals)) return waitingCard(operation, "السيارات في الطريق", `${num(operation.delivery_scheduled_meals)} وجبة موزعة على ${num(operation.delivery_trip_count)} سيارة`);
    if (!operation.site_receipt_approved) return actionCard(operation, "استلام السيارات والوجبات", `${num(operation.delivery_verified_meals)} وجبة وصلت بإثبات السائقين`, `<button class="btn btn-dark ift-primary" data-site-receipt="${esc(operation.name)}" data-arrived="${operation.delivery_verified_meals}">اعتماد الاستلام</button>`);
    if (!operation.authority_inspection_approved) return actionCard(operation, "فحص مفتش التغذية", "سجل اسم المفتش والفحص والصورة قبل توزيع الوجبات.", `<button class="btn btn-dark ift-primary" data-inspection="${esc(operation.name)}">تسجيل واعتماد الفحص</button>`);
    if (!reports.length) return actionCard(operation, "تجهيز مهام المشرفين", "أنشئ التكليفات من خطة المشرفين الشهرية.", `<button class="btn btn-dark ift-primary" data-generate="${esc(operation.name)}">تجهيز مهام المشرفين</button>`);
    const pending = reports.filter(report => !report.manager_approved).length;
    if (pending) return waitingCard(operation, "متابعة المشرفين", `بانتظار اكتمال واعتماد ${num(pending)} تقرير أدناه.`);
    return actionCard(operation, "إرسال التقرير المجمع", "جميع تقارير المشرفين معتمدة وجاهزة للإدارة.", `<button class="btn btn-dark ift-primary" data-finalize="${esc(operation.name)}">إرسال التقرير للإدارة</button>`);
  }

  function siteReports() {
    if (!data.reports.length) return "";
    return `<div class="ift-section-title"><h2>المشرفون</h2><span>${num(data.reports.length)}</span></div><section class="ift-report-list">${data.reports.map(report => `
      <article class="ift-report-card"><div><span class="ift-state ${report.manager_approved ? "done" : report.report_submitted ? "working" : "waiting"}">${report.manager_approved ? "معتمد" : report.report_submitted ? "جاهز للمراجعة" : report.received_meals ? "لدى المشرف" : "بانتظار التسليم"}</span><h3>${esc(report.supervisor_name)}</h3><p>${num(report.planned_meals)} وجبة · ${num(report.cartons)} كرتون</p></div>
      <div class="ift-actions stacked">${!report.received_meals ? `<button class="btn btn-dark" data-receive="${esc(report.name)}" data-planned="${report.planned_meals || 0}">تسليم الوجبات والعهدة</button>` : ""}${report.report_submitted && !report.manager_approved ? `<button class="btn btn-dark" data-approve="${esc(report.name)}">اعتماد تقرير المشرف</button>` : ""}<button class="btn btn-default" data-report="${esc(report.name)}">عرض التقرير والصور</button></div></article>`).join("")}</section>`;
  }

  function supervisorCards(onlyMine = true) {
    const reports = (data.reports || []).filter(report => !onlyMine || report.supervisor_user === frappe.session.user);
    if (!reports.length) return empty("تم إسناد مهمة الإشراف لك، وبانتظار تسليم مدير الموقع لمهمة اليوم");
    return `<section class="ift-task-list">${reports.map(report => {
      if (report.manager_approved) return doneCard({project_title: report.supervisor_name}, "اعتمد مدير الموقع تقريرك", `${num(report.distributed_meals)} وجبة موزعة`, report.approved_at);
      const assistants = report.assistants || [];
      const owners = report.owners || [];
      return `<article class="ift-task-card focus"><span class="ift-state ${report.received_meals ? "working" : "waiting"}">${report.received_meals ? "مهمتك الآن" : "بانتظار التسليم"}</span>
        <h2>${esc(report.supervisor_name)}</h2><div class="ift-big-number"><b>${num(report.planned_meals)}</b><span>وجبة · ${num(report.cartons)} كرتون</span></div>
        <h3 class="ift-subhead">المساعدون</h3>${assistants.length ? `<div class="ift-person-list">${assistants.map(person => `<div><span><b>${esc(person.assistant_name)}</b><small>${esc(person.mobile_no)}</small></span>${person.attendance_status === "لم يسجل / Not Marked" ? `<span><button class="btn btn-xs btn-dark" data-assistant="${esc(report.name)}" data-assistant-row="${esc(person.name)}" data-status="حاضر / Present">حاضر</button><button class="btn btn-xs btn-default" data-assistant="${esc(report.name)}" data-assistant-row="${esc(person.name)}" data-status="غائب / Absent">غائب</button></span>` : `<b>${esc(person.attendance_status)}</b>`}</div>`).join("")}</div>` : `<p class="ift-muted">لا يوجد مساعدون مسجلون.</p>`}
        <h3 class="ift-subhead">أصحاب السفر والمواقع</h3>${owners.length ? `<div class="ift-person-list">${owners.map(owner => `<div><span><b>${esc(owner.table_owner_name)}</b><small>${esc(owner.distribution_point)} · ${esc(owner.mobile_no)}</small></span>${owner.owner_confirmed ? `<b class="ift-check">تم التسليم</b>` : report.received_meals ? `<button class="btn btn-xs btn-dark" data-owner="${esc(report.name)}" data-owner-row="${esc(owner.name)}" data-planned="${owner.planned_meals || 0}">تأكيد التسليم</button>` : ""}</div>`).join("")}</div>` : `<p class="ift-muted">لا يوجد أصحاب سفر مسجلون.</p>`}
        ${report.report_submitted ? `<div class="ift-success">تم إرسال التقرير إلى مدير الموقع</div>` : report.received_meals ? `<button class="btn btn-dark ift-primary" data-submit-report="${esc(report.name)}" data-received="${report.received_meals || 0}">إنهاء المهمة وإرسال التقرير</button>` : `<div class="ift-notice"><span>سيظهر زر التنفيذ بعد استلام الوجبات والعهدة من مدير الموقع.</span></div>`}
      </article>`;
    }).join("")}</section>`;
  }

  function supervisorView() {
    return supervisorCards(true);
  }

  function multiView() {
    const cards = [];
    (data.operations || []).forEach(operation => {
      (operation.my_duties || []).forEach(duty => {
        if (duty === "project_manager") cards.push(projectManagerCard(operation));
        if (duty === "kitchen") cards.push(kitchenCard(operation));
        if (duty === "delivery") cards.push(deliveryCard(operation));
        if (duty === "site") cards.push(siteOperation(operation));
      });
    });
    let html = cards.length ? `<section class="ift-task-list">${cards.join("")}</section>` : "";
    if ((data.duty_modes || []).includes("site")) html += siteReports();
    if ((data.duty_modes || []).includes("supervisor")) html += supervisorCards(true);
    return html || empty();
  }

  function actionCard(operation, title, description, action) {
    return `<article class="ift-task-card focus"><span class="ift-state working">مهمتك الآن</span><h2>${esc(title)}</h2><p>${esc(operation.project_title)}</p><div class="ift-notice"><span>${esc(description)}</span></div>${action}</article>`;
  }

  function waitingCard(operation, title, description) {
    return `<article class="ift-task-card waiting-card"><span class="ift-state waiting">بانتظار المرحلة السابقة</span><h2>${esc(title)}</h2><p>${esc(operation.project_title)}</p><div class="ift-notice"><span>${esc(description)}</span></div></article>`;
  }

  function doneCard(operation, title, description, completedAt) {
    return `<article class="ift-task-card completed"><span class="ift-complete-icon">✓</span><span class="ift-state done">مكتمل</span><h2>${esc(title)}</h2><p>${esc(operation.project_title || "")}</p><div class="ift-big-number small"><b>${esc(description)}</b>${completedAt ? `<span>${esc(time(completedAt))}</span>` : ""}</div></article>`;
  }

  function render() {
    const labels = {
      administration: "الإدارة · تسجيل البيانات واعتماد المشروع ومتابعة المهام",
      project_manager: "مدير المشروع · متابعة اليوم فقط",
      kitchen: "مشرف المطبخ · اعتماد مرحلة المطبخ",
      delivery: "مشرف التوصيل · اعتماد مرحلة التحميل والتوصيل",
      site: "مدير الموقع · اعتماد الاستلام والتوزيع",
      supervisor: "المشرف الميداني · تنفيذ وتسليم مهمة اليوم",
      multi: "مهام إفطار الصائم المسندة لهذا الحساب"
    };
    const titles = {administration: "إدارة إفطار الصائم", project_manager: "متابعة المشروع", kitchen: "مهمة المطبخ", delivery: "مهمة التوصيل", site: "مهمة الموقع", supervisor: "مهمة المشرف", multi: "مهامي في إفطار الصائم"};
    $root.find(".ift-title").text(titles[data.mode] || "إفطار الصائم");
    $root.find(".ift-role").text(labels[data.mode] || "المهمة اليومية");
    const views = {administration: adminView, project_manager: projectManagerView, kitchen: kitchenView, delivery: deliveryView, site: siteView, supervisor: supervisorView, multi: multiView};
    $root.find(".ift-content").html((views[data.mode] || (() => empty()))());
  }

  async function load() {
    const response = await call("get_team_dashboard", {date: $root.find(".ift-date").val()});
    data = response.message || data;
    render();
  }

  $root.on("click", "[data-page]", function() { frappe.set_route($(this).data("page")); });
  $root.on("click", "[data-list]", function() { frappe.set_route("List", $(this).data("list")); });
  $root.on("click", "[data-open-project]", function() { frappe.set_route("Form", "WAFD Iftar Project", $(this).data("open-project")); });
  $root.on("click", "[data-supervisors]", function() { frappe.route_options = {project: $(this).data("supervisors")}; frappe.set_route("List", "WAFD Iftar Supervisor Plan"); });
  $root.on("click", "[data-report]", function() { frappe.set_route("Form", "WAFD Iftar Supervisor Daily Report", $(this).data("report")); });
  $root.on("click", "[data-activate]", async function() { const response = await call("approve_project_plan", {project_name: $(this).data("activate")}); const count = Number(response.message?.published_count || 0); frappe.show_alert({message: `تم اعتماد المشروع وإرسال المهام إلى ${count} موظف`, indicator: "green"}, 6); load(); });
  $root.on("click", "[data-kitchen]", function() { const name = $(this).data("kitchen"); dialog("اعتماد مرحلة المطبخ", [{fieldname: "ready_meals", fieldtype: "Int", label: "العدد الجاهز", reqd: 1, default: $(this).data("ready")}, {fieldname: "shortage_reported", fieldtype: "Check", label: "يوجد نقص مواد"}, {fieldname: "shortage_notes", fieldtype: "Small Text", label: "المواد الناقصة", depends_on: "shortage_reported"}], "اعتماد المرحلة", values => call("update_kitchen", {operation_name: name, ...values, approve: 1})); });
  $root.on("click", "[data-trip]", function() { const name = $(this).data("trip"); dialog("بيانات السيارة والعهدة", [{fieldname: "bread_quantity", fieldtype: "Int", label: "أكياس الخبز", reqd: 1, default: $(this).data("bread")}, {fieldname: "tablecloths", fieldtype: "Int", label: "السفر"}, {fieldname: "waste_bags", fieldtype: "Int", label: "أكياس النفايات"}, {fieldname: "gloves", fieldtype: "Int", label: "القفازات"}, {fieldname: "shoe_covers", fieldtype: "Int", label: "غطاء الأرجل"}, upload("loading_photo", "صورة التحميل"), {fieldname: "notes", fieldtype: "Small Text", label: "ملاحظات"}], "حفظ", values => call("update_delivery_allocation", {trip_name: name, ...values})); });
  $root.on("click", "[data-dispatch]", async function() { await call("approve_delivery_dispatch", {operation_name: $(this).data("dispatch")}); frappe.show_alert({message: "تم اعتماد التحميل والتوجيه", indicator: "green"}, 5); load(); });
  $root.on("click", "[data-site-receipt]", function() { const name = $(this).data("site-receipt"); dialog("استلام الوجبات", [{fieldname: "received_meals", fieldtype: "Int", label: "العدد المستلم", reqd: 1, default: $(this).data("arrived")}], "اعتماد الاستلام", values => call("approve_site_receipt", {operation_name: name, ...values})); });
  $root.on("click", "[data-inspection]", function() { const name = $(this).data("inspection"); dialog("فحص مفتش التغذية", [{fieldname: "supervisor_name", fieldtype: "Data", label: "اسم مفتش التغذية", reqd: 1}, {fieldname: "yogurt_checked", fieldtype: "Check", label: "تم فحص الزبادي"}, {fieldname: "bread_checked", fieldtype: "Check", label: "تم فحص الخبز"}, {fieldname: "dates_checked", fieldtype: "Check", label: "تم فحص التمر"}, {fieldname: "expiry_checked", fieldtype: "Check", label: "تم فحص تواريخ الصلاحية"}, upload("photo", "صورة الفحص"), {fieldname: "notes", fieldtype: "Small Text", label: "الملاحظات"}], "اعتماد الفحص", values => call("approve_authority_inspection", {operation_name: name, ...values})); });
  $root.on("click", "[data-generate]", async function() { await call("ensure_supervisor_reports", {operation_name: $(this).data("generate")}); load(); });
  $root.on("click", "[data-receive]", function() { const name = $(this).data("receive"); dialog("تسليم المشرف", [{fieldname: "received_meals", fieldtype: "Int", label: "عدد الوجبات", reqd: 1, default: $(this).data("planned")}, {fieldname: "tablecloths", fieldtype: "Int", label: "السفر"}, {fieldname: "bread_bags", fieldtype: "Int", label: "أكياس الخبز"}, {fieldname: "waste_bags", fieldtype: "Int", label: "أكياس النفايات"}, {fieldname: "gloves", fieldtype: "Int", label: "القفازات"}, {fieldname: "shoe_covers", fieldtype: "Int", label: "غطاء الأرجل"}, upload("handover_photo", "صورة التسليم")], "اعتماد التسليم", values => call("receive_for_supervisor", {report_name: name, ...values})); });
  $root.on("click", "[data-assistant]", async function() { await call("mark_assistant_attendance", {report_name: $(this).data("assistant"), assistant_row_name: $(this).data("assistant-row"), status: $(this).data("status")}); load(); });
  $root.on("click", "[data-owner]", function() { const report = $(this).data("owner"), owner = $(this).data("owner-row"); dialog("تسليم صاحب السفرة", [{fieldname: "delivered_meals", fieldtype: "Int", label: "عدد الوجبات المسلمة", reqd: 1, default: $(this).data("planned")}, {fieldname: "notes", fieldtype: "Small Text", label: "ملاحظات"}], "تأكيد التسليم", values => call("confirm_owner_handover", {report_name: report, owner_row_name: owner, ...values})); });
  $root.on("click", "[data-submit-report]", function() { const name = $(this).data("submit-report"); dialog("إنهاء المهمة", [{fieldname: "distributed_meals", fieldtype: "Int", label: "الموزع", reqd: 1, default: $(this).data("received")}, {fieldname: "surplus_meals", fieldtype: "Int", label: "الفائض المرتجع"}, {fieldname: "preservation_meals", fieldtype: "Int", label: "المسلم لحفظ النعمة"}, {fieldname: "waste_meals", fieldtype: "Int", label: "التالف"}, {fieldname: "tables_spread_completed", fieldtype: "Check", label: "تم فرش السفر", default: 1}, {fieldname: "distribution_completed", fieldtype: "Check", label: "تم التوزيع", default: 1}, {fieldname: "cleanup_completed", fieldtype: "Check", label: "تم رفع السفر والنفايات", default: 1}, upload("distribution_photo", "صورة التوزيع"), upload("closeout_photo", "صورة رفع السفر")], "إرسال التقرير", values => call("submit_supervisor_report", {report_name: name, ...values})); });
  $root.on("click", "[data-approve]", async function() { await call("approve_supervisor_report", {report_name: $(this).data("approve")}); load(); });
  $root.on("click", "[data-finalize]", async function() { await call("finalize_daily_report", {operation_name: $(this).data("finalize")}); frappe.show_alert({message: "وصل التقرير إلى الإدارة", indicator: "green"}, 5); load(); });
  $root.on("click", "[data-send]", function() { const name = $(this).data("send"); dialog("إرسال التقرير الرسمي", [{fieldname: "recipient", fieldtype: "Data", label: "رئاسة شؤون الحرمين أو الجهة المتعاقدة", reqd: 1}], "اعتماد وإرسال", values => call("send_authority_report", {operation_name: name, ...values})); });
  $root.on("click", ".ift-refresh", load).on("change", ".ift-date", load);
  if (frappe.realtime?.on) frappe.realtime.on("wafd_iftar_task_published", () => load());
  load();
};
