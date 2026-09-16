frappe.pages["wafd-iftar-operations"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({parent: wrapper, title: __("إفطار الصائم"), single_column: true});
  $(wrapper).find(".layout-main-section").attr("dir", "rtl").html(`<div style="padding:48px;text-align:center"><b>جارٍ فتح شاشة إفطار الصائم الرئيسية…</b></div>`);
  setTimeout(() => frappe.set_route("wafd-iftar-team"), 0);
};
frappe.pages["wafd-iftar-operations"].on_page_show = function() {
  if (frappe.get_route()[0] === "wafd-iftar-operations") frappe.set_route("wafd-iftar-team");
};
