frappe.ui.form.on("WAFD Iftar Daily Operation", {
  refresh(frm) {
    frm.$wrapper.find(".wafd-mobile-stage-action").remove();
    $(document.body).find(".wafd-mobile-stage-action").remove();
    frm.$wrapper.find(".form-layout").css("padding-bottom", "");
    if (frm.is_new()) return;
    const planned = Number(frm.doc.planned_meals || 0);
    const received = Number(frm.doc.received_meals || 0);
    frm.dashboard.add_indicator(__(`المخطط: ${planned}`), "blue");
    frm.dashboard.add_indicator(__(`المستلم: ${received}`), received >= planned && planned ? "green" : "orange");


    frm.add_custom_button(__("خطط المشرفين والفرق"), () => {
      frappe.route_options = {project: frm.doc.project};
      frappe.set_route("List", "WAFD Iftar Supervisor Plan");
    });

    frm.add_custom_button(__("📷 التوثيق اليومي"), async () => {
      const roster=(await frappe.call({method:'wafd_one.wafd_one.iftar_pro.get_project_field_roster',args:{project_name:frm.doc.project}})).message||{};
      const ownerOptions=['',...(roster.table_owners||[])].join('\n');
      const d = new frappe.ui.Dialog({
        title: __("إضافة صورة للتقرير اليومي"),
        fields: [
          {fieldname:'photo',fieldtype:'Attach Image',label:__('الصورة'),reqd:1},
          {fieldname:'caption',fieldtype:'Data',label:__('وصف مختصر')},
          {fieldname:'site_label',fieldtype:'Data',label:__('الموقع'),default:frm.doc.distribution_site||''},
          {fieldname:'table_owner_name',fieldtype:'Select',label:__('صاحب السفرة'),options:ownerOptions,default:frm.doc.table_owner_name||''},
          {fieldname:'include_in_report',fieldtype:'Check',label:__('إظهار في التقرير الرسمي'),default:1}
        ],
        primary_action_label: __("حفظ الصورة"),
        async primary_action(v){
          d.hide();
          await frappe.call({
            method:'wafd_one.wafd_one.iftar_pro.add_daily_photo',
            args:{operation_name:frm.doc.name,...v},
            freeze:true,freeze_message:__('جاري حفظ الصورة...')
          });
          frappe.show_alert({message:__('تمت إضافة الصورة إلى التوثيق اليومي'),indicator:'green'},4);
          await frm.reload_doc();
        }
      });
      d.show();
    });


    frm.add_custom_button(__("التقرير اليومي الرسمي"), () => {
      const q = new URLSearchParams({doctype:frm.doctype,name:frm.doc.name,format:'WAFD Iftar Official Daily Report',no_letterhead:'0'});
      window.open('/api/method/frappe.utils.print_format.download_pdf?' + q.toString(), '_blank', 'noopener');
    }, __("الطباعة / Print"));

    frm.add_custom_button(__("نموذج التسليم والاستلام"), () => {
      frappe.route_options = { print_format: "إفطار صائم — تسليم واستلام يومي" };
      frappe.set_route("print", frm.doctype, frm.doc.name);
    }, __("الطباعة / Print"));

    frm.add_custom_button(__("فتح شاشة مهمتي"), () => {
      frappe.route_options = {project: frm.doc.project, operation: frm.doc.name};
      frappe.set_route("wafd-iftar-team");
    }, __("التشغيل / Operations"));
  }
});
