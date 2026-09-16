frappe.ui.form.on('WAFD Iftar Supervisor Daily Report', {
  refresh(frm) {
    if (frm.is_new() || frm.doc.manager_approved) return;
    const isSupervisor = frappe.user_roles.includes('WAFD Iftar Supervisor');
    if (isSupervisor && frm.doc.supervisor_user === frappe.session.user && !frm.doc.report_submitted) {
      const btn = frm.add_custom_button(__('إرسال التقرير لمدير الموقع'), async () => {
        await frm.set_value('report_submitted', 1);
        await frm.save();
        frappe.show_alert({message: __('تم إرسال التقرير لمدير الموقع'), indicator: 'green'}, 5);
      });
      btn.addClass('btn-primary');
    }
    frm.add_custom_button(__('طباعة تقرير المشرف'), () => {
      frappe.route_options = {print_format: 'تقرير مشرف إفطار الصائم اليومي'};
      frappe.set_route('print', frm.doctype, frm.doc.name);
    }, __('الطباعة / Print'));
  }
});
