frappe.pages["wafd-undertaking-team"].on_page_load = function (wrapper) {
  const roles = new Set(frappe.user_roles || []);
  const canManage = roles.has("System Manager") || roles.has("WAFD Operations Manager");
  wrapper.innerHTML = "";
  requestAnimationFrame(() => frappe.set_route(canManage ? "wafd-employee-team" : "wafd-role-home"));
};
