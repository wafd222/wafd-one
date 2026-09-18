frappe.listview_settings['WAFD Iftar Project'] = {
  add_fields: ['project_title','distribution_site','start_date','end_date','daily_meals','total_meals','status','docstatus'],
  get_indicator(doc) {
    if (doc.docstatus === 1) return [__('معتمد / Submitted'), 'green', 'docstatus,=,1'];
    if (doc.docstatus === 0) return [__('مسودة / Draft'), 'orange', 'docstatus,=,0'];
    return [__('ملغي / Cancelled'), 'red', 'docstatus,=,2'];
  },
  onload(listview) {
    if (!listview.filter_area.get_filter('docstatus')) {
      listview.filter_area.add([[listview.doctype, 'docstatus', '!=', 2]]);
    }
  }
};
