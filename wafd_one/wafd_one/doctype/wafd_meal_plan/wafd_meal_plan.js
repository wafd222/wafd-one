frappe.ui.form.on('WAFD Meal Plan', {
  setup(frm) {
    frm.set_query('hotel', () => ({ filters: frm.doc.project ? { mission: frm.doc.__onload?.mission } : {} }));
  },
  project(frm) {
    if (!frm.doc.project) return;
    frappe.db.get_value('WAFD Catering Project', frm.doc.project, ['mission']).then(r => {
      frm.doc.__onload = { mission: r.message.mission };
      frm.set_query('hotel', () => ({ filters: { mission: r.message.mission } }));
    });
  }
});
