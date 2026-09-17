frappe.pages["wafd-iftar-team"].on_page_load = function(wrapper) {
  frappe.ui.make_app_page({ parent: wrapper, title: __("إفطار صائم"), single_column: true });
};

frappe.pages["wafd-iftar-team"].on_page_show = function() {
  // RC311: the post-RC298 team workflow is retired from the UI.
  // Keep this route as a safe compatibility redirect for old bookmarks.
  frappe.set_route("wafd-iftar-operations");
};
