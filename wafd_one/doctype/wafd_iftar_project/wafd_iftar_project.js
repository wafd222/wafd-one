frappe.ui.form.on('WAFD Iftar Project', {
  refresh(frm) {
    if (frm.is_new()) {
      frm.add_custom_button(__('تحميل الوجبة الأساسية'), () => {
        frappe.call({
          method: 'wafd_one.wafd_one.doctype.wafd_iftar_project.wafd_iftar_project.get_standard_iftar_components',
          callback: (r) => {
            frm.clear_table('meal_items');
            (r.message || []).forEach(item => frm.add_child('meal_items', item));
            frm.refresh_field('meal_items');
            frm.dirty();
          }
        });
      });
    }
    if (frm.doc.docstatus === 0) {
      frm.add_custom_button(__('إعادة حساب الخطة'), () => frm.save());
    }
  },
  authority(frm) {
    if (!frm.doc.project_title && frm.doc.authority) frm.set_value('project_title', `إفطار صائم - ${frm.doc.authority.split(' / ')[0]}`);
  },
  daily_meals(frm) { calculate_cartons(frm); },
  meals_per_carton(frm) { calculate_cartons(frm); },
  reserve_cartons(frm) { calculate_cartons(frm); }
});
function calculate_cartons(frm) {
  const meals = cint(frm.doc.daily_meals);
  const per = cint(frm.doc.meals_per_carton) || 25;
  frm.set_value('daily_cartons', Math.ceil(meals / per));
  frm.set_value('total_daily_cartons', Math.ceil(meals / per) + cint(frm.doc.reserve_cartons));
}
frappe.ui.form.on('WAFD Iftar Distribution Row', {
  recipient(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row.recipient) return;
    frappe.db.get_value('WAFD Iftar Recipient', row.recipient, ['recipient_name','mobile','default_location']).then(r => {
      frappe.model.set_value(cdt, cdn, 'recipient_name', r.message.recipient_name);
      if (!row.mobile) frappe.model.set_value(cdt, cdn, 'mobile', r.message.mobile);
      if (!row.distribution_point) frappe.model.set_value(cdt, cdn, 'distribution_point', r.message.default_location);
    });
  },
  meal_quantity(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    frappe.model.set_value(cdt, cdn, 'carton_quantity', Math.ceil(cint(row.meal_quantity) / (cint(frm.doc.meals_per_carton) || 25)));
  }
});
