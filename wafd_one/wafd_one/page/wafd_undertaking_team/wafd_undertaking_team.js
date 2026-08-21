frappe.pages["wafd-undertaking-team"].on_page_load = function(wrapper) {
  // RC210: this page is admin-only. When the same Safari/browser is reused
  // after logout, Frappe can restore the manager's last route before the new
  // officer home redirect finishes. Never render the team page for officers;
  // redirect immediately so no admin UI flashes on screen.
  const roles = new Set(frappe.user_roles || []);
  const canManageTeam = roles.has("System Manager") || roles.has("WAFD Operations Manager");
  if (!canManageTeam) {
    wrapper.innerHTML = "";
    requestAnimationFrame(() => frappe.set_route("wafd-role-home"));
    return;
  }
  const page = frappe.ui.make_app_page({parent: wrapper, title: __("فريق التعهدات"), single_column: true});
  const $root = $(page.body).attr("dir", "rtl").html(`
    <div style="max-width:850px;margin:20px auto;padding:0 12px">
      <div class="frappe-card" style="padding:18px;margin-bottom:18px">
        <h3>إضافة مسؤول تعهدات</h3>
        <p class="text-muted">كل موظف يجب أن يكون له بريد دخول مستقل. جميعهم يعملون في نفس الوقت، وكل تعهد يسجل باسم منشئه.</p>
        <div class="row">
          <div class="col-md-4"><label>اسم الموظف</label><input class="form-control" id="wafd-officer-name"></div>
          <div class="col-md-4"><label>البريد الإلكتروني</label><input class="form-control" id="wafd-officer-email" type="email" dir="ltr"></div>
          <div class="col-md-4"><label>كلمة مرور مؤقتة</label><input class="form-control" id="wafd-officer-password" type="password" dir="ltr"></div>
        </div>
        <button class="btn btn-primary" id="wafd-add-officer" style="margin-top:14px">إضافة الموظف</button>
      </div>
      <div class="frappe-card" style="padding:18px"><h3>المستخدمون المخولون بالتعهدات</h3><div id="wafd-officer-list">جاري التحميل...</div></div>
    </div>`);

  function load() {
    frappe.call({method:"wafd_one.undertaking_team.list_officers", callback(r) {
      const rows = r.message || [];
      const html = rows.length ? rows.map(u => `<div style="display:flex;gap:12px;align-items:center;justify-content:space-between;padding:12px 4px;border-bottom:1px solid var(--border-color)">
        <div><b>${frappe.utils.escape_html(u.full_name || u.name)}</b><br><small dir="ltr">${frappe.utils.escape_html(u.email || u.name)}</small></div>
        <button class="btn btn-sm ${u.enabled ? 'btn-default' : 'btn-primary'} wafd-toggle" data-user="${frappe.utils.escape_html(u.name)}" data-enabled="${u.enabled ? 0 : 1}">${u.enabled ? 'إيقاف' : 'تفعيل'}</button>
      </div>`).join("") : '<p class="text-muted">لا يوجد موظفون بعد.</p>';
      $root.find("#wafd-officer-list").html(html);
      $root.find(".wafd-toggle").on("click", function(){
        frappe.call({method:"wafd_one.undertaking_team.set_officer_enabled", args:{user:$(this).data("user"), enabled:$(this).data("enabled")}, freeze:true, callback:load});
      });
    }});
  }
  $root.find("#wafd-add-officer").on("click", function(){
    const args = {first_name:$root.find("#wafd-officer-name").val(), email:$root.find("#wafd-officer-email").val(), password:$root.find("#wafd-officer-password").val()};
    frappe.call({method:"wafd_one.undertaking_team.create_officer", args, freeze:true, freeze_message:"جاري إنشاء المستخدم...", callback(r){
      if (!r.exc) { frappe.show_alert({message:"تم إنشاء حساب الموظف", indicator:"green"}); $root.find("input").val(""); load(); }
    }});
  });
  load();
};
