frappe.pages["wafd-finance-hub"].on_page_load = function(wrapper) {
  window.wafd_one_render_hub(wrapper, { title: "المالية", items: [{"label": "الفواتير", "icon": "🧾", "doctype": "WAFD Invoice"}, {"label": "التحصيل", "icon": "💳", "doctype": "WAFD Payment"}, {"label": "العقود", "icon": "📝", "doctype": "WAFD Contract"}, {"label": "تكاليف المشاريع", "icon": "💰", "doctype": "WAFD Project Cost"}, {"label": "إيرادات المشاريع", "icon": "📈", "doctype": "WAFD Project Revenue"}, {"label": "لقطات التكلفة", "icon": "📊", "doctype": "WAFD Cost Snapshot"}] });
};
