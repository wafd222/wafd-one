frappe.pages["wafd-role-home"].on_page_load = function (wrapper) {
  const roles = new Set(frappe.user_roles || []);
  const isExecutive = roles.has("System Manager") || roles.has("WAFD Operations Manager");
  const isMobile = window.matchMedia("(max-width: 900px)").matches;

  // Managers retain the approved executive command center on desktop.
  // On phones/tablets they get the compact role home first, with an explicit
  // link to the full dashboard when they need the complete management view.
  if (isExecutive && !isMobile) {
    frappe.set_route("wafd-one-dashboard");
    return;
  }

  const page = frappe.ui.make_app_page({ parent: wrapper, title: __("WAFD ONE"), single_column: true });
  const $root = $(page.body).attr("dir", "rtl");
  const currentUser = frappe.user.full_name() || frappe.session.user;
  const today = frappe.datetime.str_to_user(frappe.datetime.get_today());

  const profiles = [
    {
      role: "System Manager", title: "الإدارة", subtitle: "لوحة قيادة مختصرة للجوال",
      items: [
        { label: "لوحة الإدارة الكاملة", desc: "المؤشرات والربحية والمخاطر", icon: "▦", page: "wafd-one-dashboard", primary: true },
        { label: "التشغيل", desc: "المشاريع والخطط والإنتاج", icon: "⚙", page: "wafd-operations-hub" },
        { label: "المخزون والمشتريات", desc: "المواد والحركات والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "التوصيل", desc: "التحميل والرحلات والتسليم", icon: "➜", page: "wafd-delivery-hub" },
        { label: "المالية", desc: "الفواتير والتحصيل", icon: "ر.س", page: "wafd-finance-hub" },
        { label: "إفطار صائم", desc: "المشاريع الموسمية والتشغيل اليومي", icon: "☾", page: "wafd-iftar-operations", special: true },
        { label: "المستندات والتعهدات", desc: "المستندات والطباعة", icon: "▤", page: "wafd-documents-hub" }
      ]
    },
    {
      role: "WAFD Operations Manager", title: "مدير العمليات", subtitle: "متابعة التشغيل اليومية",
      items: [
        { label: "لوحة الإدارة الكاملة", desc: "المؤشرات والربحية والمخاطر", icon: "▦", page: "wafd-one-dashboard", primary: true },
        { label: "التشغيل", desc: "المشاريع والخطط والإنتاج", icon: "⚙", page: "wafd-operations-hub" },
        { label: "المخزون والمشتريات", desc: "المواد والحركات والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "التوصيل", desc: "التحميل والرحلات والتسليم", icon: "➜", page: "wafd-delivery-hub" },
        { label: "المالية", desc: "الفواتير والتحصيل", icon: "ر.س", page: "wafd-finance-hub" },
        { label: "إفطار صائم", desc: "المشاريع الموسمية والتشغيل اليومي", icon: "☾", page: "wafd-iftar-operations", special: true }
      ]
    },
    {
      role: "WAFD Project Manager", title: "مدير المشروع", subtitle: "إدارة المشروع والتخطيط والمتابعة",
      items: [
        { label: "المشاريع", desc: "المشاريع المسندة وحالتها", icon: "◆", doctype: "WAFD Catering Project", primary: true },
        { label: "الخطط اليومية", desc: "الكميات والفنادق اليومية", icon: "◫", doctype: "WAFD Daily Meal Plan" },
        { label: "التشغيل", desc: "الإنتاج والجودة والتغليف", icon: "⚙", page: "wafd-operations-hub" },
        { label: "التوصيل", desc: "الرحلات والتسليم والاستلام", icon: "➜", page: "wafd-delivery-hub" },
        { label: "المستندات", desc: "التعهدات والمستندات التشغيلية", icon: "▤", page: "wafd-documents-hub" },
        { label: "إفطار صائم", desc: "المشاريع الموسمية", icon: "☾", page: "wafd-iftar-operations", special: true }
      ]
    },
    {
      role: "WAFD Production Supervisor", title: "مشرف الإنتاج", subtitle: "الخطة والإنتاج والتغليف",
      items: [
        { label: "دفعات الإنتاج", desc: "تنفيذ ومتابعة دفعات الإنتاج", icon: "▦", doctype: "WAFD Production Batch", primary: true },
        { label: "الخطط اليومية", desc: "الكميات المطلوب إنتاجها", icon: "◫", doctype: "WAFD Daily Meal Plan" },
        { label: "سجلات التغليف", desc: "متابعة الكميات المعبأة", icon: "□", doctype: "WAFD Packaging Record" },
        { label: "الوصفات", desc: "مراجع الوصفات المعتمدة", icon: "≡", doctype: "WAFD Recipe" }
      ]
    },
    {
      role: "WAFD Quality Inspector", title: "مفتش الجودة", subtitle: "الفحص ونقاط التحكم الحرجة",
      items: [
        { label: "فحص الجودة", desc: "الفحوصات المطلوبة ونتائجها", icon: "✓", doctype: "WAFD Quality Inspection", primary: true },
        { label: "دفعات الإنتاج", desc: "دفعات الإنتاج المطلوب فحصها", icon: "▦", doctype: "WAFD Production Batch" },
        { label: "فحوص CCP", desc: "نقاط التحكم الحرجة", icon: "◎", doctype: "WAFD CCP Check" },
        { label: "سجلات التغليف", desc: "قراءة السجلات بعد الفحص", icon: "□", doctype: "WAFD Packaging Record" }
      ]
    },
    {
      role: "WAFD Storekeeper", title: "أمين المستودع", subtitle: "المخزون والاستلام والصرف",
      items: [
        { label: "حركات المخزون", desc: "استلام وصرف وتحويل المواد", icon: "↔", doctype: "WAFD Stock Movement", primary: true },
        { label: "أرصدة المخزون", desc: "الكميات المتاحة بالمستودعات", icon: "▥", doctype: "WAFD Stock Balance" },
        { label: "المخزون والمشتريات", desc: "كل أدوات المستودع والمشتريات", icon: "▣", page: "wafd-inventory-hub" },
        { label: "أوامر الشراء", desc: "متابعة المواد المشتراة", icon: "⌑", doctype: "WAFD Purchase Order" },
        { label: "إفطار صائم", desc: "المخزون المرتبط بالمشاريع الموسمية", icon: "☾", page: "wafd-iftar-operations", special: true }
      ]
    },
    {
      role: "WAFD Cleaning Supervisor", title: "مشرف النظافة", subtitle: "مواد النظافة المصروفة لك فقط",
      items: [
        { label: "مخزون أدوات النظافة", desc: "رصيد مستودع أدوات النظافة", icon: "✦", doctype: "WAFD Stock Balance", filters: { warehouse: "مستودع 7 - أدوات النظافة" }, primary: true },
        { label: "المواد المصروفة لي", desc: "حركات الصرف المسندة لحسابك", icon: "▤", doctype: "WAFD Stock Movement" }
      ]
    },
    {
      role: "WAFD Delivery Supervisor", title: "مشرف التوصيل", subtitle: "التحميل والرحلات والتسليم",
      items: [
        { label: "رحلات التوصيل", desc: "إدارة ومتابعة الرحلات", icon: "➜", doctype: "WAFD Delivery Trip", primary: true },
        { label: "سجلات التحميل", desc: "التحميل قبل خروج الرحلة", icon: "▣", doctype: "WAFD Loading Record" },
        { label: "سندات التسليم", desc: "التسليم للجهة المستفيدة", icon: "▤", doctype: "WAFD Delivery Note" },
        { label: "سندات الاستلام", desc: "توثيق الاستلام النهائي", icon: "✓", doctype: "WAFD Receiving Note" },
        { label: "إفطار صائم", desc: "التوصيل للمشاريع الموسمية", icon: "☾", page: "wafd-iftar-operations", special: true }
      ]
    },
    {
      role: "WAFD Driver", title: "السائق", subtitle: "رحلاتك المسندة لك فقط",
      items: [
        { label: "رحلاتي", desc: "المركبة والوجهة وحالة الرحلة", icon: "➜", doctype: "WAFD Delivery Trip", primary: true }
      ]
    },
    {
      role: "WAFD Finance User", title: "المالية", subtitle: "الفوترة والتحصيل والعقود المرجعية",
      items: [
        { label: "الفواتير", desc: "المستحقات وحالة الفواتير", icon: "ر.س", doctype: "WAFD Invoice", primary: true },
        { label: "التحصيل", desc: "الدفعات وربطها بالفواتير", icon: "✓", doctype: "WAFD Payment" },
        { label: "العقود", desc: "المرجع المالي للعقود", icon: "▤", doctype: "WAFD Contract" },
        { label: "المشاريع", desc: "المشروع المرتبط بالفاتورة", icon: "◆", doctype: "WAFD Catering Project" }
      ]
    },
    {
      role: "WAFD Approver", title: "المعتمد", subtitle: "المراجعة والاعتماد المالي",
      items: [
        { label: "المالية", desc: "الفواتير والتحصيل والمراجعة", icon: "ر.س", page: "wafd-finance-hub", primary: true },
        { label: "طلبات الاعتماد", desc: "الطلبات التي تحتاج قرارًا", icon: "✓", doctype: "WAFD Approval Request" }
      ]
    },
    {
      role: "WAFD Auditor", title: "المدقق", subtitle: "مراجعة السجلات المالية",
      items: [
        { label: "الفواتير", desc: "مراجعة الفواتير", icon: "ر.س", doctype: "WAFD Invoice", primary: true },
        { label: "التحصيل", desc: "مراجعة التحصيلات", icon: "✓", doctype: "WAFD Payment" },
        { label: "المالية", desc: "مركز المراجعة المالية", icon: "▦", page: "wafd-finance-hub" }
      ]
    }
  ];

  const profile = profiles.find((candidate) => roles.has(candidate.role)) || {
    role: "Desk User", title: "WAFD ONE", subtitle: "لا توجد أدوات تشغيلية مخصصة لهذا الحساب", items: []
  };

  function canRead(item) {
    if (!item.doctype) return true;
    try { return !frappe.model.can_read || frappe.model.can_read(item.doctype); }
    catch (e) { return true; }
  }

  const items = (profile.items || []).filter(canRead);
  const roleLabel = profile.title;
  const escapedUser = frappe.utils.escape_html(currentUser);
  const escapedRole = frappe.utils.escape_html(roleLabel);

  $root.html(`
    <div class="wafd-role-home">
      <section class="wafd-mobile-hero">
        <div class="wafd-mobile-brand">
          <div class="wafd-mobile-logo"><img src="/assets/wafd_one/images/wafd-almadinah-dashboard.png" alt="WAFD ONE"></div>
          <div>
            <span>شركة وفد المدينة لخدمات الإعاشة</span>
            <h1>WAFD ONE</h1>
            <p>${frappe.utils.escape_html(profile.subtitle || "")}</p>
          </div>
        </div>
        <div class="wafd-mobile-user">
          <div><small>المستخدم</small><strong>${escapedUser}</strong></div>
          <div><small>الدور</small><strong>${escapedRole}</strong></div>
          <div><small>التاريخ</small><strong>${frappe.utils.escape_html(today)}</strong></div>
        </div>
      </section>

      <section class="wafd-mobile-section-head">
        <div><span>مهامك</span><small>الأدوات الظاهرة مرتبطة بصلاحيات حسابك فقط</small></div>
        <span class="wafd-mobile-count">${items.length}</span>
      </section>

      <section class="wafd-mobile-grid">
        ${items.map((item, idx) => `
          <button type="button" class="wafd-mobile-card ${item.primary ? "is-primary" : ""} ${item.special ? "is-special" : ""}" data-idx="${idx}">
            <b>${item.icon || "•"}</b>
            <span>${frappe.utils.escape_html(item.label || "")}</span>
            <small>${frappe.utils.escape_html(item.desc || "")}</small>
            <i>←</i>
          </button>`).join("")}
      </section>

      ${items.length ? "" : `<div class="wafd-mobile-empty">لا توجد أدوات متاحة لهذا الحساب. راجع الدور والصلاحيات مع مسؤول النظام.</div>`}

      <section class="wafd-mobile-security-note">
        <b>WAFD ONE</b>
        <span>تظهر لك فقط الوظائف والبيانات التي يسمح بها دورك في النظام.</span>
      </section>
    </div>
  `);

  $root.find(".wafd-mobile-card").on("click", function () {
    const item = items[Number($(this).attr("data-idx"))];
    if (!item) return;
    if (item.page) {
      frappe.set_route(item.page);
      return;
    }
    if (item.doctype) {
      frappe.set_route("List", item.doctype, item.filters || {});
    }
  });
};
