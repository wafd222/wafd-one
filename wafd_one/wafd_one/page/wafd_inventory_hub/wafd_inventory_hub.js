frappe.pages['wafd-inventory-hub'].on_page_load = function(wrapper) {
  const inventoryRoles = ["System Manager", "WAFD Operations Manager", "WAFD Storekeeper", "WAFD Production Supervisor", "WAFD Project Manager"];

  window.wafd_one_render_hub(wrapper, {
    title: "المخزون والمشتريات",
    items: [
      {"label": "حركات المخزون", "icon": "↔️", "doctype": "WAFD Stock Movement", "roles": inventoryRoles},
      {"label": "أرصدة المخزون", "icon": "📊", "doctype": "WAFD Stock Balance", "roles": inventoryRoles},
      {"label": "المستودعات والثلاجات", "icon": "🏬", "doctype": "WAFD Warehouse", "roles": inventoryRoles},
      {"label": "المواد", "icon": "🧺", "doctype": "WAFD Ingredient", "roles": inventoryRoles},
      {"label": "أوامر الشراء", "icon": "🛒", "doctype": "WAFD Purchase Order", "roles": inventoryRoles},
      {"label": "خطط المشتريات", "icon": "📋", "doctype": "WAFD Procurement Plan", "roles": inventoryRoles},

      {"label": "مخزون أدوات النظافة", "icon": "🧹", "doctype": "WAFD Stock Balance", "roles": ["WAFD Cleaning Supervisor", "WAFD Storekeeper", "WAFD Operations Manager", "System Manager"], "filters": {"warehouse": "مستودع 7 - أدوات النظافة"}},
      {"label": "المواد / حركات الصرف الخاصة بي", "icon": "🧴", "doctype": "WAFD Stock Movement", "roles": ["WAFD Cleaning Supervisor"]},
      {"label": "صرف أدوات النظافة", "icon": "🧴", "new_doctype": "WAFD Stock Movement", "roles": ["WAFD Storekeeper", "WAFD Operations Manager", "System Manager"], "defaults": {"movement_type": "صرف / Issue", "source_warehouse": "مستودع 7 - أدوات النظافة", "issue_purpose": "نظافة / Cleaning"}},
      {"label": "إدخال الرصيد الافتتاحي", "icon": "🧮", "new_doctype": "WAFD Stock Movement", "roles": ["WAFD Storekeeper", "WAFD Operations Manager", "System Manager"], "defaults": {"movement_type": "تسوية / Adjustment"}}
    ]
  });
};
