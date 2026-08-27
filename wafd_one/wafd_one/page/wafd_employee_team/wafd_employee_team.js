frappe.pages["wafd-employee-team"].on_page_load = function (wrapper) {
  const userRoles = new Set(frappe.user_roles || []);
  const canManage = userRoles.has("System Manager") || userRoles.has("WAFD Operations Manager");
  if (!canManage) {
    wrapper.innerHTML = "";
    requestAnimationFrame(() => frappe.set_route("wafd-role-home"));
    return;
  }

  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("إدارة الموظفين"),
    single_column: true,
  });
  const lang = localStorage.getItem("wafd_lang") || "ar";
  const arabic = lang === "ar";
  const tr = (ar, en) => (arabic ? ar : en);
  const esc = (value) => frappe.utils.escape_html(String(value || ""));
  const $root = $(page.body).attr("dir", arabic ? "rtl" : "ltr");
  let employees = [];
  let roleOptions = [];

  const roleLabel = (role) => {
    const option = roleOptions.find((item) => item.role === role);
    return option ? (arabic ? option.label : option.label_en) : role;
  };

  const normalizeMobile = (value) => {
    const mobile = String(value || "").trim()
      .replace(/[٠-٩]/g, (digit) => "٠١٢٣٤٥٦٧٨٩".indexOf(digit))
      .replace(/[۰-۹]/g, (digit) => "۰۱۲۳۴۵۶۷۸۹".indexOf(digit));
    const digits = mobile.replace(/\D/g, "");
    if (/^05\d{8}$/.test(digits)) return `+966${digits.slice(1)}`;
    if (/^9665\d{8}$/.test(digits)) return `+${digits}`;
    if (/^009665\d{8}$/.test(digits)) return `+${digits.slice(2)}`;
    if (mobile.includes("+") || digits.startsWith("00")) return `+${digits.startsWith("00") ? digits.slice(2) : digits}`;
    return digits;
  };

  const goBack = () => {
    if (window.history.length > 1) window.history.back();
    else frappe.set_route("wafd-role-home");
  };

  $root.html(`
    <style>
      .wafd-employee-shell{max-width:980px;margin:18px auto 44px;padding:0 12px;color:#1d1e22}
      .wafd-employee-inline-nav{display:none}.wafd-employee-inline-back{width:42px;height:42px;align-items:center;justify-content:center;border:1px solid rgba(118,91,32,.42);border-radius:12px;background:#f5f0e4;box-shadow:0 3px 12px rgba(0,0,0,.08)}.wafd-employee-inline-back-arrow{display:block;width:13px;height:13px;border-left:3px solid #6e531b;border-bottom:3px solid #6e531b;transform:rotate(45deg);margin-left:5px}
      .wafd-employee-card{background:#fff;border:1px solid #e8e2d6;border-radius:22px;padding:22px;box-shadow:0 10px 30px rgba(22,23,27,.045);margin-bottom:16px}
      .wafd-employee-card h2{font-size:24px;font-weight:850;margin:0 0 7px}.wafd-employee-card p{color:#74777d;font-size:13px;margin:0 0 18px;line-height:1.75}
      .wafd-employee-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}.wafd-employee-field{min-width:0}.wafd-employee-field label{display:block;font-weight:750;font-size:13px;margin-bottom:6px}
      .wafd-employee-field input,.wafd-employee-field select{width:100%;height:45px;border:1px solid #ded8cb;border-radius:12px;background:#faf9f6;padding:8px 11px;color:#1d1e22;outline:none}
      .wafd-employee-field input:focus,.wafd-employee-field select:focus{border-color:#a98232;box-shadow:0 0 0 3px rgba(169,130,50,.12)}
      .wafd-employee-actions{display:flex;gap:10px;align-items:center;margin-top:16px}.wafd-employee-primary{border:0;border-radius:12px;background:#1d1e22;color:#fff;padding:11px 18px;font-weight:800}
      .wafd-employee-toolbar{display:grid;grid-template-columns:1fr 240px;gap:10px;margin:14px 0}.wafd-employee-toolbar input,.wafd-employee-toolbar select{height:42px;border:1px solid #ded8cb;border-radius:11px;padding:8px 11px;background:#faf9f6}
      .wafd-employee-row{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(180px,.8fr) auto;gap:14px;align-items:center;padding:15px 4px;border-bottom:1px solid #eee9df}.wafd-employee-row:last-child{border-bottom:0}
      .wafd-employee-identity b,.wafd-employee-identity small{display:block}.wafd-employee-identity small{color:#777b82;margin-top:3px}.wafd-employee-role{display:flex;flex-wrap:wrap;gap:6px}.wafd-role-badge,.wafd-status-badge{display:inline-flex;align-items:center;border-radius:999px;padding:6px 10px;font-size:11px;font-weight:750}.wafd-role-badge{background:#f4eddd;color:#765b23}.wafd-status-badge.is-on{background:#e8f4ea;color:#2e6a38}.wafd-status-badge.is-off{background:#f3e8e8;color:#8b3030}
      .wafd-row-actions{display:flex;gap:7px;justify-content:flex-end}.wafd-row-actions button{border:1px solid #ddd6c8;border-radius:10px;background:#fff;padding:8px 11px;font-size:12px;font-weight:750;white-space:nowrap}.wafd-row-actions button.is-stop{color:#963434}.wafd-empty{padding:30px 10px;text-align:center;color:#7b7e83}.wafd-driver-note{display:none;margin-top:6px;color:#916d25;font-size:11px}
      @media(max-width:700px){.wafd-employee-shell{padding:0 9px;margin-top:10px}.wafd-employee-inline-nav{display:flex;justify-content:flex-end;margin:0 0 10px}.wafd-employee-inline-back{display:flex}.wafd-employee-card{padding:17px;border-radius:18px}.wafd-employee-card h2{font-size:21px}.wafd-employee-form{grid-template-columns:1fr}.wafd-employee-toolbar{grid-template-columns:1fr}.wafd-employee-row{grid-template-columns:1fr;gap:9px}.wafd-row-actions{justify-content:flex-start;flex-wrap:wrap}.wafd-row-actions button{flex:1}.wafd-employee-role{justify-content:flex-start}}
    </style>
    <div class="wafd-employee-shell">
      <div class="wafd-employee-inline-nav"><button type="button" class="wafd-employee-inline-back" aria-label="${tr("رجوع", "Back")}" title="${tr("رجوع", "Back")}"><span class="wafd-employee-inline-back-arrow" aria-hidden="true"></span></button></div>
      <section class="wafd-employee-card">
        <h2>${tr("إضافة موظف", "Add employee")}</h2>
        <p>${tr("أنشئ لكل موظف حساب دخول مستقل وحدد مهمته. يمكن إضافة أكثر من موظف للمهمة نفسها، وتظهر لكل موظف الأدوات التي تسمح بها مهمته فقط.", "Create an independent login for each employee and assign one operational task. Multiple employees can share the same task, and each sees only the tools allowed by that task.")}</p>
        <div class="wafd-employee-form">
          <div class="wafd-employee-field"><label>${tr("اسم الموظف", "Employee name")}</label><input id="wafd-employee-name" autocomplete="name"></div>
          <div class="wafd-employee-field"><label>${tr("البريد الإلكتروني", "Email")}</label><input id="wafd-employee-email" type="email" dir="ltr" autocomplete="email"></div>
          <div class="wafd-employee-field"><label>${tr("المهمة", "Task")}</label><select id="wafd-employee-role"><option value="">${tr("اختر المهمة", "Select task")}</option></select></div>
          <div class="wafd-employee-field"><label>${tr("رقم الجوال", "Mobile number")}</label><input id="wafd-employee-mobile" type="tel" dir="ltr" autocomplete="tel" placeholder="05xxxxxxxx / +9665xxxxxxxx"><small class="wafd-driver-note">${tr("رقم الجوال مطلوب للسائق، وتُقبل الصيغة المحلية أو الدولية.", "A driver mobile is required; local and international formats are accepted.")}</small></div>
          <div class="wafd-employee-field"><label>${tr("كلمة مرور مؤقتة", "Temporary password")}</label><input id="wafd-employee-password" type="password" dir="ltr" minlength="8" autocomplete="new-password"></div>
        </div>
        <div class="wafd-employee-actions"><button type="button" class="wafd-employee-primary" id="wafd-add-employee">${tr("إنشاء حساب الموظف", "Create employee account")}</button></div>
      </section>
      <section class="wafd-employee-card">
        <h2>${tr("الموظفون والمهمات", "Employees and tasks")}</h2>
        <div class="wafd-employee-toolbar">
          <input id="wafd-employee-search" placeholder="${tr("بحث بالاسم أو البريد", "Search by name or email")}">
          <select id="wafd-employee-filter"><option value="">${tr("جميع المهمات", "All tasks")}</option></select>
        </div>
        <div id="wafd-employee-list"><div class="wafd-empty">${tr("جاري التحميل...", "Loading...")}</div></div>
      </section>
    </div>
  `);

  function fillRoleSelectors() {
    const options = roleOptions.map((item) => `<option value="${esc(item.role)}">${esc(arabic ? item.label : item.label_en)}</option>`).join("");
    $root.find("#wafd-employee-role").html(`<option value="">${tr("اختر المهمة", "Select task")}</option>${options}`);
    $root.find("#wafd-employee-filter").html(`<option value="">${tr("جميع المهمات", "All tasks")}</option>${options}`);
  }

  function filteredEmployees() {
    const query = String($root.find("#wafd-employee-search").val() || "").trim().toLowerCase();
    const role = $root.find("#wafd-employee-filter").val();
    return employees.filter((employee) => {
      const haystack = `${employee.full_name || ""} ${employee.email || employee.name || ""}`.toLowerCase();
      return (!query || haystack.includes(query)) && (!role || (employee.roles || []).includes(role));
    });
  }

  function renderList() {
    const rows = filteredEmployees();
    if (!rows.length) {
      $root.find("#wafd-employee-list").html(`<div class="wafd-empty">${tr("لا يوجد موظفون مطابقون.", "No matching employees.")}</div>`);
      return;
    }
    $root.find("#wafd-employee-list").html(rows.map((employee) => {
      const roles = (employee.roles || []).map((role) => `<span class="wafd-role-badge">${esc(roleLabel(role))}</span>`).join("");
      return `<div class="wafd-employee-row">
        <div class="wafd-employee-identity"><b>${esc(employee.full_name || employee.name)}</b><small dir="ltr">${esc(employee.email || employee.name)}</small></div>
        <div class="wafd-employee-role">${roles}<span class="wafd-status-badge ${employee.enabled ? "is-on" : "is-off"}">${employee.enabled ? tr("مفعّل", "Active") : tr("موقوف", "Disabled")}</span></div>
        <div class="wafd-row-actions">
          <button type="button" class="wafd-change-role" data-user="${esc(employee.name)}">${tr("تغيير المهمة", "Change task")}</button>
          <button type="button" class="wafd-toggle-employee ${employee.enabled ? "is-stop" : ""}" data-user="${esc(employee.name)}" data-enabled="${employee.enabled ? 0 : 1}">${employee.enabled ? tr("إيقاف", "Disable") : tr("تفعيل", "Enable")}</button>
        </div>
      </div>`;
    }).join(""));
  }

  function load() {
    frappe.call({
      method: "wafd_one.employee_team.list_employees",
      callback: (response) => {
        const message = response.message || {};
        employees = message.employees || [];
        roleOptions = message.roles || [];
        fillRoleSelectors();
        renderList();
      },
    });
  }

  function changeRole(employee) {
    const labelToRole = {};
    const labels = roleOptions.map((item) => {
      const label = arabic ? item.label : item.label_en;
      labelToRole[label] = item.role;
      return label;
    });
    const currentRole = (employee.roles || []).length === 1 ? roleLabel(employee.roles[0]) : "";
    const dialog = new frappe.ui.Dialog({
      title: tr("تغيير مهمة الموظف", "Change employee task"),
      fields: [
        {fieldname: "role_label", fieldtype: "Select", label: tr("المهمة الجديدة", "New task"), options: labels, default: currentRole, reqd: 1},
        {fieldname: "mobile", fieldtype: "Data", label: tr("رقم الجوال", "Mobile number"), default: employee.mobile_no || ""},
      ],
      primary_action_label: tr("حفظ المهمة", "Save task"),
      primary_action: (values) => {
        const role = labelToRole[values.role_label];
        frappe.call({
          method: "wafd_one.employee_team.set_employee_role",
          args: {user: employee.name, role, mobile: normalizeMobile(values.mobile)},
          freeze: true,
          freeze_message: tr("جاري تحديث المهمة...", "Updating task..."),
          callback: (response) => {
            if (!response.exc) {
              dialog.hide();
              frappe.show_alert({message: tr("تم تحديث مهمة الموظف", "Employee task updated"), indicator: "green"});
              load();
            }
          },
        });
      },
    });
    dialog.show();
  }

  $root.on("change", "#wafd-employee-role", function () {
    $root.find(".wafd-driver-note").toggle($(this).val() === "WAFD Driver");
  });
  $root.on("blur", "#wafd-employee-mobile", function () {
    $(this).val(normalizeMobile($(this).val()));
  });
  $root.on("click", ".wafd-employee-inline-back", goBack);
  $root.on("input change", "#wafd-employee-search, #wafd-employee-filter", renderList);
  $root.on("click", ".wafd-change-role", function () {
    const employee = employees.find((item) => item.name === $(this).attr("data-user"));
    if (employee) changeRole(employee);
  });
  $root.on("click", ".wafd-toggle-employee", function () {
    const user = $(this).attr("data-user");
    const enabled = Number($(this).attr("data-enabled"));
    const run = () => frappe.call({
      method: "wafd_one.employee_team.set_employee_enabled",
      args: {user, enabled},
      freeze: true,
      callback: (response) => {
        if (!response.exc) {
          frappe.show_alert({message: enabled ? tr("تم تفعيل الموظف", "Employee enabled") : tr("تم إيقاف الموظف", "Employee disabled"), indicator: enabled ? "green" : "orange"});
          load();
        }
      },
    });
    if (enabled) run();
    else frappe.confirm(tr("سيتم إغلاق جلسات الموظف فورًا وإيقاف دخوله. هل تريد المتابعة؟", "The employee will be signed out immediately and their login disabled. Continue?"), run);
  });
  $root.on("click", "#wafd-add-employee", function () {
    const args = {
      first_name: $root.find("#wafd-employee-name").val(),
      email: $root.find("#wafd-employee-email").val(),
      role: $root.find("#wafd-employee-role").val(),
      mobile: normalizeMobile($root.find("#wafd-employee-mobile").val()),
      password: $root.find("#wafd-employee-password").val(),
    };
    frappe.call({
      method: "wafd_one.employee_team.create_employee",
      args,
      freeze: true,
      freeze_message: tr("جاري إنشاء حساب الموظف...", "Creating employee account..."),
      callback: (response) => {
        if (!response.exc) {
          frappe.show_alert({message: tr("تم إنشاء حساب الموظف", "Employee account created"), indicator: "green"});
          $root.find("#wafd-employee-name, #wafd-employee-email, #wafd-employee-mobile, #wafd-employee-password").val("");
          $root.find("#wafd-employee-role").val("").trigger("change");
          load();
        }
      },
    });
  });

  load();
};
