frappe.pages["wafd-operations-hub"].on_page_load = function(wrapper) {
  window.wafd_one_render_hub(wrapper, { title: "التشغيل", items: [{"label": "المشاريع", "icon": "📁", "doctype": "WAFD Catering Project"}, {"label": "الخطط اليومية", "icon": "📅", "doctype": "WAFD Daily Meal Plan"}, {"label": "دفعات الإنتاج", "icon": "🏭", "doctype": "WAFD Production Batch"}, {"label": "فحص الجودة", "icon": "✅", "doctype": "WAFD Quality Inspection"}, {"label": "سجلات التغليف", "icon": "📦", "doctype": "WAFD Packaging Record"}, {"label": "سجلات التحميل", "icon": "🚛", "doctype": "WAFD Loading Record"}] });
};
