frappe.pages["wafd-master-data-hub"].on_page_load = function(wrapper) {
  window.wafd_one_render_hub(wrapper, { title: "البيانات المرجعية", items: [{"label": "الفنادق", "icon": "🏨", "doctype": "WAFD Hotel"}, {"label": "البعثات والعملاء", "icon": "🌍", "doctype": "WAFD Mission"}, {"label": "الوصفات", "icon": "📖", "doctype": "WAFD Recipe"}, {"label": "مكونات الأغذية", "icon": "🥘", "doctype": "WAFD Ingredient"}, {"label": "المستودعات والثلاجات", "icon": "🏬", "doctype": "WAFD Warehouse"}, {"label": "الموردون", "icon": "🤝", "doctype": "WAFD Supplier"}] });
};
