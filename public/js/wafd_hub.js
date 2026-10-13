window.wafd_one_render_hub = function(wrapper, config) {
  const page = frappe.ui.make_app_page({ parent: wrapper, title: __(config.title || "WAFD ONE"), single_column: true });
  const roles = new Set(frappe.user_roles || []);
  const elevated = roles.has("System Manager") || roles.has("WAFD Operations Manager");
  const canRole = item => !item.roles || elevated || item.roles.some(r => roles.has(r));
  const canRead = item => {
    if (!item.doctype) return true;
    try { return !frappe.model.can_read || frappe.model.can_read(item.doctype); } catch (e) { return true; }
  };
  const items = (config.items || []).filter(item => canRole(item) && canRead(item));
  const html = `<div class="wafd-hub-wrap" dir="rtl"><div class="wafd-hub-grid">${items.map((item, idx) => `
    <button class="wafd-hub-card" data-idx="${idx}" type="button">
      <span class="wafd-hub-icon">${item.icon || "•"}</span>
      <span class="wafd-hub-label">${frappe.utils.escape_html(__(item.label || ""))}</span>
      <span class="wafd-hub-arrow">‹</span>
    </button>`).join("")}</div>${items.length ? "" : `<div class="text-muted wafd-hub-empty">${__("لا توجد عناصر متاحة حسب صلاحياتك / No items available for your role")}</div>`}</div>`;
  $(page.body).html(html);
  $(page.body).find('.wafd-hub-card').on('click', function() {
    const item = items[Number($(this).attr('data-idx'))];
    if (!item) return;
    if (item.new_doctype) { frappe.new_doc(item.new_doctype, item.defaults || {}); return; }
    if (item.doctype) { frappe.set_route('List', item.doctype, item.filters || {}); return; }
    if (item.page) { frappe.set_route(item.page); }
  });
};
