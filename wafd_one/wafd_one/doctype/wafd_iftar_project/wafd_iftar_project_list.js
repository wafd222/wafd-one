frappe.listview_settings['WAFD Iftar Project'] = {
  add_fields: ['project_title','distribution_site','start_date','end_date','daily_meals','total_meals','status','docstatus'],
  get_indicator(doc) {
    if (doc.docstatus === 1) return [__('معتمد / Submitted'), 'green', 'docstatus,=,1'];
    if (doc.docstatus === 0) return [__('مسودة / Draft'), 'orange', 'docstatus,=,0'];
    return [__('ملغي / Cancelled'), 'red', 'docstatus,=,2'];
  },
  formatters: {
    project_title(value, df, doc) {
      const title = frappe.utils.escape_html(value || doc.name || '');
      const site = frappe.utils.escape_html(doc.distribution_site || '');
      const dates = [doc.start_date, doc.end_date].filter(Boolean).map(d => frappe.datetime.str_to_user(d)).join(' — ');
      const meals = frappe.format(doc.total_meals || doc.daily_meals || 0, {fieldtype:'Int'});
      return `<div><b>${title}</b><div class="wafd-project-list-sub">${frappe.utils.escape_html(doc.name)} · ${site}${dates ? ' · '+dates : ''} · ${meals} وجبة</div></div>`;
    }
  },
  onload(listview) {
    if (!listview.filter_area.get_filter('docstatus')) {
      listview.filter_area.add([[listview.doctype, 'docstatus', '!=', 2]]);
    }
  }
};
